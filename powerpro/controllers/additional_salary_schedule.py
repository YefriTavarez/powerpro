"""Opt-in recurring payroll allocation. Legacy inputs retain native behavior."""
import json
import frappe
from frappe.utils import cint, getdate
from powerpro.payroll_rules.additional_salary_schedule import MODES, allocation

MODE = "pp_recurring_distribution"
EFFECTIVE = "pp_recurring_distribution_from"
SNAPSHOT = "pp_recurring_salary_snapshot"
FIELDS = ["name", "employee", "company", "currency", "salary_component", "type", "amount",
          "is_recurring", "from_date", "to_date", "payroll_date", "docstatus", "disabled",
          "overwrite_salary_structure_amount", "deduct_full_tax_on_selected_payroll_date", MODE, EFFECTIVE]


def installed():
    meta = frappe.get_meta("Additional Salary")
    return meta.has_field(MODE) and meta.has_field(EFFECTIVE)


def second_day():
    if frappe.db.exists("DocType", "Employee Supplement Settings"):
        value = frappe.db.get_single_value("Employee Supplement Settings", "second_quincena_day")
        if value is not None and str(value) != "":
            return cint(value)
    return 16


def lock_employee(employee):
    if employee:
        # Same employee lock order as the monthly payroll engine. Configuration
        # and submission serialize before either reads or changes an allocation.
        frappe.db.sql("SELECT name FROM `tabEmployee` WHERE name=%s FOR UPDATE", (employee,))


def _applies(row, start, end):
    if row.docstatus != 1 or row.disabled:
        return False
    if row.is_recurring:
        return bool(row.from_date and row.to_date and getdate(row.from_date) <= end <= getdate(row.to_date))
    return bool(row.payroll_date and start <= getdate(row.payroll_date) <= end)


def _configured_for(row, end):
    return bool(row.get(MODE) and row.get(EFFECTIVE) and getdate(row.get(EFFECTIVE)) <= end)


def add_components(slip, component_type):
    """Return False for native fallback; True when this method handled the list.

    Runs inside SalarySlip.calculate_component_amounts, before tax calculation,
    equally for in-memory preview, draft save, submission and standard APIs.
    """
    if not installed() or not slip.employee or not slip.start_date or not slip.end_date:
        return False
    start, end = getdate(slip.start_date), getdate(slip.end_date)
    kind = "Earning" if component_type == "earnings" else "Deduction"
    rows = frappe.get_all("Additional Salary", filters={"employee": slip.employee, "type": kind},
                          fields=FIELDS, order_by="creation, name", limit_page_length=0)
    configured = {r.name for r in rows if _configured_for(r, end)}
    for row in rows:
        if row.get(MODE) and not row.get(EFFECTIVE) and _applies(row, start, end):
            frappe.throw("Falta Aplicar desde el Mes en " + row.name)
    active_configured = {r.name for r in rows if r.name in configured and _applies(r, start, end)}
    stale = any(r.additional_salary in configured for r in slip.get(component_type))
    if not active_configured and not stale:
        return False
    if active_configured and slip.salary_slip_based_on_timesheet:
        frappe.throw("La aplicación por quincena no es compatible con recibos basados en hojas de tiempo.")
    precision = frappe.get_precision("Salary Detail", "amount", currency=slip.currency)
    calendar_day = second_day()
    selected, plans, overwritten = [], [], set()
    for row in rows:
        if not _applies(row, start, end):
            continue
        amount = row.amount
        if row.name in configured:
            if not row.is_recurring:
                frappe.throw("La programación requiere un Salario Adicional recurrente: " + row.name)
            if row.company != slip.company or row.currency != slip.currency:
                frappe.throw("La empresa o moneda del recurrente no coincide con el recibo: " + row.name)
            if start < getdate(row.get(EFFECTIVE)):
                frappe.throw("La aplicación cambia dentro del período del recibo: " + row.name)
            try:
                amount = float(allocation(row.amount, row.get(MODE), start, end, slip.payroll_frequency,
                                          second_day=calendar_day, precision=precision))
            except ValueError as exc:
                frappe.throw(str(exc))
            plans.append({"additional_salary": row.name, "salary_component": row.salary_component,
                          "distribution": row.get(MODE), "effective_from": str(row.get(EFFECTIVE)),
                          "monthly_base": row.amount, "allocated_base": amount})
            if not amount:
                continue
        if row.overwrite_salary_structure_amount:
            if row.salary_component in overwritten:
                frappe.throw("Existen varios salarios adicionales que sustituyen el mismo componente en este período: " + row.salary_component)
            overwritten.add(row.salary_component)
        native = frappe._dict(name=row.name, component=row.salary_component, type=row.type,
                              amount=amount, is_recurring=row.is_recurring,
                              overwrite=row.overwrite_salary_structure_amount,
                              deduct_full_tax_on_selected_payroll_date=row.deduct_full_tax_on_selected_payroll_date)
        selected.append(native)
    # Remove only opt-in source rows, including disabled/expired inputs. This is
    # needed when a draft is recalculated or its period changes; never save it here.
    slip.set(component_type, [r for r in slip.get(component_type) if r.additional_salary not in configured])
    from hrms.payroll.doctype.salary_slip.salary_slip import get_salary_component_data
    for item in selected:
        component = get_salary_component_data(item.component)
        remove_zero = frappe.get_cached_value("Salary Component", item.component, "remove_if_zero_valued")
        if not item.amount and remove_zero:
            continue
        slip.update_component_row(component, item.amount, component_type, item, is_recurring=item.is_recurring)
    snapshot = json.loads(slip.get(SNAPSHOT) or "{}")
    snapshot[component_type] = {"start_date": str(start), "end_date": str(end), "rows": plans}
    slip.set(SNAPSHOT, json.dumps(snapshot, default=str, ensure_ascii=False, sort_keys=True))
    return True


def validate_schedule(doc, method=None):
    mode, effective = doc.get(MODE), doc.get(EFFECTIVE)
    old = doc.get_doc_before_save()
    old_mode = old.get(MODE) if old else None
    if not mode and not old_mode:
        return
    fields = [MODE, EFFECTIVE, "amount", "employee", "company", "currency", "salary_component", "is_recurring", "from_date", "to_date"]
    changed = not old or any(str(old.get(f) or "") != str(doc.get(f) or "") for f in fields)
    if mode:
        if not doc.is_recurring or mode not in MODES or not effective:
            frappe.throw("Indique Es recurrente, Aplicación en Nómina y Aplicar desde el Mes.")
        if getdate(effective).day != 1:
            frappe.throw("Aplicar desde el Mes debe ser el primer día del mes. La selección determina la quincena, no esta fecha.")
        if not doc.from_date or not doc.to_date or getdate(effective) > getdate(doc.to_date):
            frappe.throw("La aplicación debe coincidir con un mes dentro de la vigencia del Salario Adicional.")
        if doc.get("pp_supplement_key") or doc.get("custom_igc_supplement_key"):
            frappe.throw("Los complementos automáticos conservan su programación en el Empleado.")
        if frappe.db.exists("DocType", "Employee Supplement Existing Salary") and frappe.db.exists(
            "Employee Supplement Existing Salary", {"additional_salary": doc.name, "treatment": "Coverage"}
        ):
            frappe.throw("Este registro cubre un complemento del Empleado; no cambie su distribución desde Salario Adicional.")
        # Validate value/calendar without changing the stored monthly amount.
        try:
            allocation(doc.amount, mode, "2026-01-01", "2026-01-31", "Monthly", second_day=second_day())
        except ValueError as exc:
            frappe.throw(str(exc))
    if not changed:
        return
    dates = [getdate(v) for v in (effective, old.get(EFFECTIVE) if old else None) if v]
    if not dates:
        frappe.throw("No elimine la fecha de una programación existente.")
    starts = [getdate(v) for v in (doc.from_date, old.from_date if old else None) if v]
    cutoff = max(min(dates), min(starts)) if starts else min(dates)
    ends = [getdate(v) for v in (doc.to_date, old.to_date if old else None) if v]
    through = max(ends) if ends else None
    employees = sorted({e for e in (doc.employee, old.employee if old else None) if e})
    for employee in employees:
        lock_employee(employee)
        filters = {"employee": employee, "docstatus": 1, "end_date": [">=", cutoff]}
        if through:
            filters["start_date"] = ["<=", through]
        posted = frappe.get_all("Salary Slip", filters=filters, fields=["name"], limit_page_length=1)
        if posted:
            frappe.throw("Ya existe una nómina validada desde el mes afectado (" + posted[0].name + "). No se cambia su programación ni se repite el descuento; cierre la vigencia anterior y registre el cambio para un mes no procesado.")


@frappe.whitelist()
def configure_distribution(name, distribution, effective_from, expected_modified):
    """Explicit configuration only. Never submit/cancel/recalculate any payroll."""
    if not installed():
        frappe.throw("Ejecute primero la migración de Aplicación en Nómina.")
    doc = frappe.get_doc("Additional Salary", name)
    doc.check_permission("write")
    employee = doc.employee
    lock_employee(employee)
    doc = frappe.get_doc("Additional Salary", name, for_update=True)
    doc.check_permission("write")
    if doc.employee != employee:
        frappe.throw("El empleado del registro cambió. Recargue antes de continuar.")
    if str(doc.modified) != str(expected_modified):
        frappe.throw("El Salario Adicional cambió. Recargue antes de configurar la aplicación.")
    if doc.docstatus == 2 or doc.disabled:
        frappe.throw("El registro debe estar activo y no cancelado.")
    if distribution not in MODES:
        frappe.throw("Seleccione una aplicación en nómina válida.")
    doc.set(MODE, distribution)
    doc.set(EFFECTIVE, effective_from)
    doc.save()
    return {"name": doc.name, "distribution": doc.get(MODE), "effective_from": str(doc.get(EFFECTIVE)),
            "modified": str(doc.modified), "payroll_documents_changed": 0}
