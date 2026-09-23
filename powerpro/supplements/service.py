"""Frappe adapter. All writes share the caller's transaction; never commit or enqueue here."""
import json
from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import cint, getdate, today

from powerpro.supplements import rules

SETTINGS = "Employee Supplement Settings"
REVISION = "Employee Supplement Revision"
SNAPSHOT = "pp_employee_supplements"
_AUTHORITY = object()
AS_FIELDS = ["name", "employee", "company", "currency", "salary_component", "type", "amount",
             "docstatus", "disabled", "is_recurring", "from_date", "to_date", "payroll_date",
             "overwrite_salary_structure_amount", "pp_supplement_key", "pp_supplement_field",
             "pp_supplement_start", "pp_supplement_end", "pp_supplement_monthly", "pp_supplement_treatment"]


def fail(message):
    frappe.throw(_(str(message)), title=_("Complementos de nómina"))


def settings(active=True):
    if not frappe.db.exists("DocType", SETTINGS):
        return None
    config = frappe.get_single(SETTINGS)
    return config if not active or config.enabled else None


def lock_employee(employee):
    frappe.db.sql("select name from `tabEmployee` where name=%s for update", (employee,))


def current_rows(doctype, filters, fields, order_by="name", limit=None):
    # MariaDB uses REPEATABLE-READ on the target bench. A lock alone does not refresh
    # previous consistent reads; use locking/current reads for payroll decisions.
    return frappe.db.get_values(doctype, filters, fields, as_dict=True, for_update=True,
                                order_by=order_by, limit=limit)


def internal(doc):
    return getattr(doc, "_pp_supplement_authority", None) is _AUTHORITY


def trusted(doc):
    doc._pp_supplement_authority = _AUTHORITY
    return doc


def amounts(employee):
    try:
        return {field: str(rules.money(employee.get(field), 4)) for field in rules.FIELDS}
    except ValueError as exc:
        fail(exc)


def employee_currency(employee):
    return employee.salary_currency or frappe.db.get_value("Company", employee.company, "default_currency")


def component_valid(name):
    component = frappe.get_doc("Salary Component", name)
    if component.type != "Earning" or any(component.get(k) for k in (
        "disabled", "depends_on_payment_days", "statistical_component", "do_not_include_in_total",
        "do_not_include_in_accounts", "variable_based_on_taxable_salary", "is_flexible_benefit",
    )):
        fail(f"{name}: use un ingreso habilitado, pagable y sin prorrateo por días.")
    return component


def classifications(config, field):
    coverage = {r.additional_salary for r in config.existing_salaries
                if r.treatment == "Coverage" and r.source_field == field}
    independent = {r.additional_salary for r in config.existing_salaries if r.treatment == "Independent"}
    return coverage, independent


def write_revision(employee, effective, legacy_changes=None):
    doc = frappe.get_doc(dict(doctype=REVISION, employee=employee.name, company=employee.company,
        currency=employee_currency(employee), effective_from=effective, amounts=json.dumps(amounts(employee)),
        source_modified=employee.modified, legacy_changes=json.dumps(legacy_changes or []),
        revision_key=rules.key(employee.company, employee.name, "revision", effective, effective)))
    trusted(doc).insert(ignore_permissions=True)
    return doc


def seed_history(config):
    if not config.enabled:
        return
    for name in frappe.get_all("Employee", filters={"company": config.company, "status": "Active"}, pluck="name", order_by="name"):
        lock_employee(name)
        if frappe.db.exists(REVISION, {"employee": name}):
            continue
        employee = frappe.get_doc("Employee", name, for_update=True)
        if employee_currency(employee) != config.currency:
            fail(f"{name}: moneda distinta de la configurada.")
        write_revision(employee, config.effective_from)


def latest_prepared(employee):
    slips = current_rows("Salary Slip", filters={"employee": employee, "docstatus": ["<", 2]},
                           fields=["end_date", SNAPSHOT])
    ends = [getdate(r.end_date) for r in slips if r.get(SNAPSHOT)]
    salaries = current_rows("Additional Salary", filters={"employee": employee, "docstatus": ["<", 2],
        "pp_supplement_key": ["is", "set"]}, fields=["pp_supplement_end"])
    ends += [getdate(r.pp_supplement_end) for r in salaries if r.pp_supplement_end]
    return max(ends) if ends else None


def validate_employee(doc, method=None):
    doc._pp_supplement_revision_date = None
    config = settings(active=False)
    if not config or doc.company != config.company or (not config.enabled and not frappe.db.exists(REVISION, {"employee": doc.name})):
        # Once enrolled, changing company/currency must not orphan historical entitlements.
        if not doc.is_new() and frappe.db.exists("DocType", REVISION) and frappe.db.exists(REVISION, {"employee": doc.name}):
            old = doc.get_doc_before_save()
            if old and old.company != doc.company:
                fail("No cambie la empresa de un empleado con historial de complementos.")
        return
    if not doc.is_new():
        lock_employee(doc.name)
    old = doc.get_doc_before_save()
    changed = old is None or amounts(doc) != amounts(old)
    if old and employee_currency(doc) != employee_currency(old):
        fail("No cambie la moneda de un empleado con complementos sin una transición explícita.")
    if not changed and frappe.db.exists(REVISION, {"employee": doc.name}):
        return
    if doc.status != "Active":
        if changed and old:
            fail("No cambie importes de complementos de un empleado inactivo.")
        return
    if employee_currency(doc) != config.currency:
        fail("La moneda del empleado no coincide con los complementos.")
    effective = doc.get("pp_supplements_effective_from")
    if not effective:
        fail("Indique desde cuándo aplica el cambio de complementos.")
    effective = getdate(effective)
    if effective < max(getdate(today()), getdate(config.effective_from)) or effective.day not in (1, cint(config.second_quincena_day)):
        fail("Use una vigencia presente o futura que comience una quincena y no preceda la activación.")
    last = frappe.db.get_value(REVISION, {"employee": doc.name}, "effective_from", order_by="effective_from desc", for_update=True)
    if last and effective <= getdate(last):
        fail("La nueva vigencia debe ser posterior a la última revisión registrada.")
    prepared = latest_prepared(doc.name) if not doc.is_new() else None
    if prepared and effective <= prepared:
        fail("El cambio alcanza un período ya preparado. Use una vigencia posterior.")
    assignments = current_rows("Salary Structure Assignment", filters={"employee": doc.name,
        "docstatus": 1, "from_date": ["<=", effective]}, fields=["salary_structure"],
        order_by="from_date desc, creation desc", limit=1)
    if assignments:
        frequency = frappe.db.get_value("Salary Structure", assignments[0].salary_structure, "payroll_frequency")
        if frequency == "Monthly" and effective.day != 1:
            fail("Los cambios de un empleado mensual deben comenzar el primer día del mes.")
    doc._pp_supplement_revision_date = effective


def record_employee(doc, method=None):
    effective = getattr(doc, "_pp_supplement_revision_date", None)
    if not effective:
        return
    config = settings(active=False)
    old = doc.get_doc_before_save()
    changed = set(rules.FIELDS) if not old else {f for f in rules.FIELDS if amounts(old)[f] != amounts(doc)[f]}
    changes = []
    for row in config.existing_salaries:
        if row.treatment != "Coverage" or row.source_field not in changed:
            continue
        salary = frappe.get_doc("Additional Salary", row.additional_salary, for_update=True)
        if salary.employee != doc.name or salary.docstatus != 1 or salary.disabled:
            continue
        if salary.is_recurring and getdate(salary.to_date) >= effective:
            if getdate(salary.from_date) >= effective:
                fail(f"{salary.name}: existe una cobertura futura. Debe conciliarse antes de cambiar el importe.")
            # Includes historical slips predating this feature: never cut off an already prepared payroll.
            if current_rows("Salary Slip", {"employee": doc.name, "docstatus": ["<", 2],
                                                 "end_date": [">=", effective]}, ["name"]):
                fail(f"{salary.name}: el cierre de vigencia alcanzaría recibos existentes.")
            changes.append(dict(additional_salary=salary.name, old_to_date=str(salary.to_date),
                                new_to_date=str(effective - timedelta(days=1))))
            salary.to_date = effective - timedelta(days=1)
            salary.validate_dates()
            # Core locks to_date after submit. Narrow app-controlled closure, audited by Version and revision.
            salary.flags.ignore_validate_update_after_submit = True
            trusted(salary).save(ignore_permissions=True)
        elif not salary.is_recurring and salary.payroll_date and getdate(salary.payroll_date) >= effective:
            fail(f"{salary.name}: hay una cobertura puntual futura que debe conciliarse.")
    write_revision(doc, effective, changes)


def active_additionals(employee, component, start, end):
    rows = current_rows("Additional Salary", filters={"employee": employee, "salary_component": component,
        "docstatus": ["<", 2], "disabled": 0}, fields=AS_FIELDS)
    for row in rows:
        if row.docstatus == 0 and rules.applies(dict(row, docstatus=1), start, end):
            fail(f"{row.name}: hay un Additional Salary en borrador para el período. No se generará otra copia.")
    return [row for row in rows if rules.applies(row, start, end)]


def revision_for(employee, start, end):
    rows = current_rows(REVISION, filters={"employee": employee, "effective_from": ["<=", end]},
                         fields=["name", "effective_from", "amounts", "currency", "company"],
                         order_by="effective_from desc")
    if not rows or getdate(rows[0].effective_from) > getdate(start):
        fail(f"{employee}: no hay una vigencia única que cubra todo el período.")
    return rows[0]


def prepare_slip(slip, method=None):
    # before_insert only: previews never create payroll documents; reject client-supplied snapshots.
    slip.set(SNAPSHOT, None)
    config = settings()
    if not config or slip.company != config.company:
        return
    if not slip.start_date or not slip.end_date:
        if not slip.payroll_entry:
            fail("Indique un Payroll Entry con período definido para calcular los complementos.")
        source = frappe.get_doc("Payroll Entry", slip.payroll_entry)
        for field in ("start_date", "end_date", "payroll_frequency"):
            if not slip.get(field):
                slip.set(field, source.get(field))
    if getdate(slip.end_date) < getdate(config.effective_from):
        return
    if not slip.payroll_entry:
        fail("Los complementos automáticos requieren crear el recibo desde Payroll Entry.")
    from powerpro.controllers import mixed_frequency_payroll as mixed
    mixed.prepare_slip(slip)
    entry = frappe.get_doc("Payroll Entry", slip.payroll_entry)
    entry.check_permission("write")
    if entry.docstatus != 1 or entry.company != slip.company or slip.employee not in {r.employee for r in entry.employees}:
        fail("El recibo requiere una nómina confirmada de la misma empresa que incluya al empleado.")
    if slip.salary_slip_based_on_timesheet or slip.currency != config.currency or entry.currency != config.currency:
        fail("Los complementos requieren nómina por período y la moneda configurada.")
    if not mixed.enabled(entry) and any(str(slip.get(k)) != str(entry.get(k)) for k in ("start_date", "end_date", "payroll_frequency")):
        fail("El período del recibo no coincide con Payroll Entry.")
    lock_employee(slip.employee)
    if current_rows("Salary Slip", {"employee": slip.employee, "docstatus": ["<", 2],
        "start_date": ["<=", slip.end_date], "end_date": [">=", slip.start_date]}, ["name"]):
        fail("Ya existe un recibo que se superpone con este período.")
    employee = frappe.get_doc("Employee", slip.employee, for_update=True)
    if employee.status != "Active" or employee.company != config.company or employee_currency(employee) != config.currency:
        fail("El empleado no está activo o no coincide con la empresa/moneda de los complementos.")
    latest = current_rows(REVISION, {"employee": slip.employee}, ["amounts"],
                          order_by="effective_from desc", limit=1)
    if not latest or json.loads(latest[0].amounts) != amounts(employee):
        fail("Los importes actuales del empleado no coinciden con su historial. Registre una vigencia antes de generar.")
    revision = revision_for(slip.employee, slip.start_date, slip.end_date)
    values = json.loads(revision.amounts)
    # Validate before writing any Additional Salary. The payroll worker rolls back on failure.
    plans = []
    assignments = current_rows("Salary Structure Assignment", filters={"employee": slip.employee, "docstatus": 1,
        "from_date": ["<=", slip.start_date]}, fields=["salary_structure"], order_by="from_date desc, creation desc", limit=1)
    if not assignments:
        fail("El empleado no tiene estructura asignada al inicio del período.")
    structure = frappe.get_doc("Salary Structure", assignments[0].salary_structure)
    if structure.payroll_frequency != slip.payroll_frequency or structure.company != config.company or structure.currency != config.currency:
        fail("La estructura asignada no coincide con la frecuencia, empresa o moneda del recibo.")
    for mapping in config.mappings:
        field, component = mapping.source_field, mapping.salary_component
        component_valid(component)
        if any(r.salary_component == component for r in list(structure.earnings) + list(structure.deductions)):
            fail(f"{component}: ya figura en la estructura. Elimine la doble fuente antes de automatizar.")
        try:
            amount = rules.period_amount(values[field], slip.payroll_frequency, slip.start_date, slip.end_date,
                                         cint(config.second_quincena_day), cint(config.amount_precision))
        except ValueError as exc:
            fail(exc)
        identity = rules.key(slip.company, slip.employee, field, slip.start_date, slip.end_date)
        candidates = active_additionals(slip.employee, component, slip.start_date, slip.end_date)
        for row in candidates:
            if row.company != slip.company or row.currency != slip.currency or row.type != "Earning":
                fail(f"{row.name}: empresa, moneda o tipo incompatible con el recibo.")
            if row.pp_supplement_key and (row.pp_supplement_key != identity or row.pp_supplement_field != field):
                fail(f"{row.name}: un complemento automático de otro período se superpone.")
        coverage, independent = classifications(config, field)
        try:
            existing = rules.resolve(amount, candidates, coverage, independent, identity)
        except ValueError as exc:
            fail(exc)
        if not existing and frappe.db.get_value("Additional Salary", {"pp_supplement_key": identity}, for_update=True):
            fail("El complemento del período fue cancelado o deshabilitado. No se regenerará silenciosamente.")
        plans.append(dict(source_field=field, salary_component=component, monthly_amount=values[field],
                          amount=str(amount), key=identity, additional_salary=existing))
    snapshot = dict(version=1, employee=slip.employee, company=slip.company, currency=slip.currency,
        payroll_entry=slip.payroll_entry, start_date=str(slip.start_date), end_date=str(slip.end_date),
        payroll_frequency=slip.payroll_frequency, revision=revision.name, rows=plans)
    for row in plans:
        if not row["additional_salary"] and rules.money(row["amount"], 4):
            salary = frappe.get_doc(dict(doctype="Additional Salary", employee=slip.employee,
                company=slip.company, currency=slip.currency, salary_component=row["salary_component"],
                type="Earning", amount=float(row["amount"]), payroll_date=slip.end_date,
                is_recurring=0, overwrite_salary_structure_amount=0, ref_doctype=REVISION,
                ref_docname=revision.name, pp_supplement_payroll_entry=slip.payroll_entry, pp_supplement_key=row["key"],
                pp_supplement_field=row["source_field"], pp_supplement_start=slip.start_date,
                pp_supplement_end=slip.end_date, pp_supplement_monthly=float(row["monthly_amount"])))
            trusted(salary).insert(ignore_permissions=True)
            salary.submit()
            row["additional_salary"] = salary.name
    slip.set(SNAPSHOT, json.dumps(snapshot, sort_keys=True, ensure_ascii=False))
    slip._pp_prepared_supplements = slip.get(SNAPSHOT)


def validate_slip(slip, method=None):
    # The app can be installed on other sites in the same bench without this patch.
    if not frappe.get_meta("Salary Slip").has_field(SNAPSHOT):
        return
    saved = None if slip.is_new() else frappe.db.get_value("Salary Slip", slip.name, SNAPSHOT, for_update=True)
    raw = slip.get(SNAPSHOT)
    expected = getattr(slip, "_pp_prepared_supplements", None) if slip.is_new() else saved
    if raw != expected:
        fail("No se puede alterar el registro de complementos del recibo.")
    if not raw:
        return
    lock_employee(slip.employee)
    snapshot = json.loads(raw)
    for name in ("employee", "company", "currency", "payroll_entry", "payroll_frequency", "start_date", "end_date"):
        if str(slip.get(name)) != str(snapshot[name]):
            fail("El recibo cambió de empleado, moneda, nómina o período después de preparar los complementos.")
    config = settings(active=False)
    for row in snapshot["rows"]:
        candidates = active_additionals(slip.employee, row["salary_component"], slip.start_date, slip.end_date)
        coverage, independent = classifications(config, row["source_field"])
        # Saved provenance keeps existing coverage stable even with the feature disabled later.
        if row["additional_salary"]:
            coverage.add(row["additional_salary"])
        try:
            existing = rules.resolve(row["amount"], candidates, coverage, independent, row["key"])
        except ValueError as exc:
            fail(exc)
        if existing != row["additional_salary"]:
            fail("La cobertura del complemento cambió desde la preparación del recibo.")
        if existing:
            earnings = [r for r in slip.earnings if r.get("additional_salary") == existing]
            if len(earnings) != 1 or rules.money(earnings[0].amount, 4) != rules.money(row["amount"], 4):
                fail(f"{existing}: el recibo no contiene el importe completo del complemento.")


def protect_additional(doc, method=None):
    if internal(doc):
        return
    if not doc.is_new():
        lock_employee(doc.employee)
    old = doc.get_doc_before_save()
    managed = doc.get("pp_supplement_key") or (old and old.get("pp_supplement_key"))
    if managed:
        fail("Este Additional Salary es automático. Corrija la vigencia en Employee; no lo edite ni cancele directamente.")
    if any(doc.get(k) for k in ("pp_supplement_field", "pp_supplement_start", "pp_supplement_end", "pp_supplement_monthly", "pp_supplement_payroll_entry")):
        fail("Los campos de origen del complemento solo los asigna PowerPro.")
    config = settings(active=False)
    if not config:
        return
    associated = any(r.additional_salary == doc.name for r in config.existing_salaries)
    if associated:
        fail("Este adicional está conciliado con complementos. Su cobertura histórica debe conservarse.")
    if not config.enabled or doc.company != config.company:
        return
    if doc.salary_component in {r.salary_component for r in config.mappings}:
        lock_employee(doc.employee)
        if doc.pp_supplement_treatment != "Independent":
            fail("Indique Independent si este pago se suma al complemento fijo; concilie las coberturas en la configuración.")
        if doc.overwrite_salary_structure_amount:
            fail("Un pago independiente no puede reemplazar el componente de la estructura.")
