# Copyright (c) 2026, PowerPro contributors
# For license information, please see license.txt

import re
from collections import Counter

import frappe
from frappe import _
from frappe.utils import getdate

from powerpro.payroll_rules.dominican_republic import get_isr_scale, get_tss_rule


EXPECTED_RATES = {
    "employee_afp": 2.87,
    "employee_ars": 3.04,
    "employer_afp": 7.10,
    "employer_ars": 7.09,
    "employer_infotep": 1.00,
}

EMPLOYER_COMPONENTS = (
    "AFP Empleador",
    "ARS Empleador",
    "INFOTEP Empleador",
    "SRL Empleador",
)


@frappe.whitelist()
def get_payroll_preflight(payroll_entry):
    """Return a read-only readiness report for one saved Payroll Entry."""
    entry = frappe.get_doc("Payroll Entry", payroll_entry)
    if not frappe.has_permission("Payroll Entry", "read", doc=entry):
        frappe.throw(_("Not permitted to read Payroll Entry {0}").format(entry.name), frappe.PermissionError)

    issues = []
    employees = [row.employee for row in entry.employees if row.employee]

    _check_entry_fields(entry, employees, issues)
    _check_assignments(entry, employees, issues)
    _check_period_conflicts(entry, employees, issues)
    _check_employee_compliance_data(entry, employees, issues)
    _check_payroll_rules(entry, issues)
    _check_additional_salary(entry, employees, issues)

    counts = Counter(issue["severity"] for issue in issues)
    status = "blocked" if counts["blocker"] else "ready_with_warnings" if counts["warning"] else "ready"

    return {
        "payroll_entry": entry.name,
        "status": status,
        "summary": {
            "employees": len(employees),
            "blockers": counts["blocker"],
            "warnings": counts["warning"],
            "information": counts["info"],
        },
        "issues": issues,
        "read_only": True,
        "enforced": False,
    }


@frappe.whitelist()
def get_payroll_preview(payroll_entry):
    """Calculate Salary Slips in memory without inserting or saving documents."""
    entry = frappe.get_doc("Payroll Entry", payroll_entry)
    if not frappe.has_permission("Payroll Entry", "read", doc=entry) or not frappe.has_permission(
        "Salary Slip", "read"
    ):
        frappe.throw(_("Not permitted to preview payroll."), frappe.PermissionError)

    preflight = get_payroll_preflight(entry.name)
    if preflight["summary"]["blockers"]:
        return {
            "payroll_entry": entry.name,
            "status": "blocked",
            "currency": entry.currency,
            "preflight": preflight,
            "rows": [],
            "errors": [],
            "totals": {},
            "read_only": True,
            "saved_documents": 0,
        }

    employees = [row.employee for row in entry.employees if row.employee]
    existing = {
        row.employee: row
        for row in frappe.get_all(
            "Salary Slip",
            filters={
                "employee": ["in", employees],
                "payroll_entry": entry.name,
                "docstatus": ["<", 2],
            },
            fields=["name", "employee", "gross_pay", "total_deduction", "net_pay"],
            order_by="creation desc",
        )
    }

    rows = []
    errors = []
    component_totals = Counter()
    calculated_totals = Counter()
    stored_totals = Counter()
    for employee in employees:
        try:
            slip = _calculate_salary_slip_in_memory(entry, employee)
            employer_total = 0.0
            employer_afp_ars = 0.0
            for detail in [*slip.earnings, *slip.deductions]:
                component_totals[detail.salary_component] += float(detail.amount or 0)
                if detail.salary_component in EMPLOYER_COMPONENTS:
                    employer_total += float(detail.amount or 0)
                if detail.salary_component in ("AFP Empleador", "ARS Empleador"):
                    employer_afp_ars += float(detail.amount or 0)

            stored = existing.get(employee)
            calculated_totals["gross_pay"] += float(slip.gross_pay or 0)
            calculated_totals["total_deduction"] += float(slip.total_deduction or 0)
            calculated_totals["net_pay"] += float(slip.net_pay or 0)
            calculated_totals["employer_afp_ars"] += employer_afp_ars
            calculated_totals["employer_contributions"] += employer_total
            if stored:
                stored_totals["net_pay"] += float(stored.net_pay or 0)
            rows.append({
                "employee": employee,
                "employee_name": slip.employee_name,
                "salary_structure": slip.salary_structure,
                "gross_pay": _money(slip.gross_pay),
                "total_deduction": _money(slip.total_deduction),
                "net_pay": _money(slip.net_pay),
                "employer_afp_ars": _money(employer_afp_ars),
                "employer_contributions": _money(employer_total),
                "existing_salary_slip": stored.name if stored else None,
                "stored_net_pay": _money(stored.net_pay) if stored else None,
                "net_pay_delta": _money(float(slip.net_pay or 0) - float(stored.net_pay or 0)) if stored else None,
            })
        except Exception as exc:
            errors.append({"employee": employee, "message": str(exc)})
        finally:
            if frappe.message_log:
                frappe.message_log.clear()

    comparable_rows = [row for row in rows if row["stored_net_pay"] is not None]
    changed_rows = [row for row in comparable_rows if abs(row["net_pay_delta"]) >= 0.01]
    totals = {
        "employees": len(rows),
        "existing_slips": len(comparable_rows),
        "changed_existing_slips": len(changed_rows),
        "gross_pay": _money(calculated_totals["gross_pay"]),
        "total_deduction": _money(calculated_totals["total_deduction"]),
        "net_pay": _money(calculated_totals["net_pay"]),
        "stored_net_pay": _money(stored_totals["net_pay"]),
        "net_pay_delta": _money(calculated_totals["net_pay"] - stored_totals["net_pay"]),
        "employer_afp_ars": _money(calculated_totals["employer_afp_ars"]),
        "employer_contributions": _money(calculated_totals["employer_contributions"]),
        "components": {key: _money(value) for key, value in sorted(component_totals.items())},
    }

    status = "preview_with_errors" if errors else "preview_with_differences" if changed_rows else "preview_ready"

    return {
        "payroll_entry": entry.name,
        "status": status,
        "currency": entry.currency,
        "preflight": preflight,
        "rows": rows,
        "errors": errors,
        "totals": totals,
        "read_only": True,
        "saved_documents": 0,
    }


def _calculate_salary_slip_in_memory(entry, employee):
    slip = frappe.get_doc({
        "doctype": "Salary Slip",
        "employee": employee,
        "salary_slip_based_on_timesheet": entry.salary_slip_based_on_timesheet,
        "payroll_frequency": entry.payroll_frequency,
        "start_date": entry.start_date,
        "end_date": entry.end_date,
        "company": entry.company,
        "posting_date": entry.posting_date,
        "deduct_tax_for_unclaimed_employee_benefits": entry.deduct_tax_for_unclaimed_employee_benefits,
        "deduct_tax_for_unsubmitted_tax_exemption_proof": entry.deduct_tax_for_unsubmitted_tax_exemption_proof,
        "payroll_entry": entry.name,
        "exchange_rate": entry.exchange_rate,
        "currency": entry.currency,
    })
    slip.get_emp_and_working_day_details()
    if not slip.salary_structure:
        frappe.throw(_("No active Salary Structure found for employee {0}.").format(employee))
    slip.set_salary_structure_assignment()
    slip.calculate_net_pay()
    return slip


def _money(value):
    return round(float(value or 0), 2)


def _add_issue(issues, severity, code, title, message, records=None):
    records = records or []
    issues.append({
        "severity": severity,
        "code": code,
        "title": title,
        "message": message,
        "record_count": len(records),
        "records": records[:25],
    })


def _check_entry_fields(entry, employees, issues):
    required = {
        "company": _("Company"),
        "currency": _("Currency"),
        "payroll_payable_account": _("Payroll Payable Account"),
        "payroll_frequency": _("Payroll Frequency"),
        "start_date": _("Start Date"),
        "end_date": _("End Date"),
        "posting_date": _("Posting Date"),
    }
    missing = [label for fieldname, label in required.items() if not entry.get(fieldname)]
    if missing:
        _add_issue(
            issues,
            "blocker",
            "PE_REQUIRED_FIELDS",
            _("Payroll Entry is incomplete"),
            _("Complete these required fields: {0}.").format(", ".join(missing)),
            missing,
        )

    if entry.start_date and entry.end_date and getdate(entry.start_date) > getdate(entry.end_date):
        _add_issue(
            issues,
            "blocker",
            "PE_INVALID_PERIOD",
            _("Payroll period is invalid"),
            _("Start Date must be on or before End Date."),
        )

    if not employees:
        _add_issue(
            issues,
            "blocker",
            "PE_NO_EMPLOYEES",
            _("No employees selected"),
            _("Use Get Employees and review the resulting employee list before generating slips."),
        )


def _check_assignments(entry, employees, issues):
    if not employees or not all((entry.company, entry.currency, entry.payroll_frequency, entry.end_date)):
        return

    structures = frappe.get_all(
        "Salary Structure",
        filters={
            "docstatus": 1,
            "is_active": "Yes",
            "company": entry.company,
            "currency": entry.currency,
            "payroll_frequency": entry.payroll_frequency,
            "salary_slip_based_on_timesheet": entry.salary_slip_based_on_timesheet,
        },
        pluck="name",
    )
    if not structures:
        _add_issue(
            issues,
            "blocker",
            "PE_NO_ACTIVE_STRUCTURE",
            _("No matching active Salary Structure"),
            _("No submitted active structure matches the company, currency, frequency, and timesheet mode."),
        )
        return

    filters = {
        "docstatus": 1,
        "employee": ["in", employees],
        "company": entry.company,
        "currency": entry.currency,
        "salary_structure": ["in", structures],
        "from_date": ["<=", entry.end_date],
    }
    if entry.payroll_payable_account:
        filters["payroll_payable_account"] = entry.payroll_payable_account

    assigned = set(frappe.get_all("Salary Structure Assignment", filters=filters, pluck="employee"))
    missing = sorted(set(employees) - assigned)
    if missing:
        _add_issue(
            issues,
            "blocker",
            "PE_MISSING_ASSIGNMENTS",
            _("Employees lack an eligible Salary Structure Assignment"),
            _("{0} selected employee(s) do not have a submitted assignment matching this payroll.").format(len(missing)),
            missing,
        )


def _check_period_conflicts(entry, employees, issues):
    if not employees or not entry.start_date or not entry.end_date:
        return

    slips = frappe.get_all(
        "Salary Slip",
        filters={
            "employee": ["in", employees],
            "start_date": entry.start_date,
            "end_date": entry.end_date,
            "docstatus": ["<", 2],
        },
        fields=["name", "employee", "payroll_entry", "docstatus"],
        order_by="employee, name",
    )
    conflicts = [row for row in slips if row.payroll_entry != entry.name]
    current = [row for row in slips if row.payroll_entry == entry.name]

    if conflicts:
        labels = [f"{row.employee}: {row.name}" for row in conflicts]
        _add_issue(
            issues,
            "blocker",
            "PE_CONFLICTING_SLIPS",
            _("Conflicting Salary Slips already exist"),
            _("{0} non-cancelled slip(s) exist for the same employees and exact period outside this Payroll Entry.").format(len(conflicts)),
            labels,
        )

    if current:
        draft_count = sum(1 for row in current if row.docstatus == 0)
        submitted_count = sum(1 for row in current if row.docstatus == 1)
        _add_issue(
            issues,
            "info",
            "PE_EXISTING_SLIPS",
            _("This Payroll Entry already has Salary Slips"),
            _("Current entry: {0} draft and {1} submitted slip(s).").format(draft_count, submitted_count),
        )


def _check_employee_compliance_data(entry, employees, issues):
    if not employees:
        return

    meta = frappe.get_meta("Employee")
    fields = ["name", "employee_name", "holiday_list"]
    optional_fields = [
        "custom_personal_id",
        "health_insurance_provider",
        "health_insurance_no",
    ]
    fields.extend(fieldname for fieldname in optional_fields if meta.has_field(fieldname))
    rows = frappe.get_all("Employee", filters={"name": ["in", employees]}, fields=fields, order_by="name")

    if meta.has_field("custom_personal_id"):
        missing_ids = [row.name for row in rows if not row.get("custom_personal_id")]
        malformed_ids = [
            row.name
            for row in rows
            if row.get("custom_personal_id") and not _is_dominican_id_shape(row.custom_personal_id)
        ]
        if missing_ids:
            _add_issue(
                issues,
                "warning",
                "EMP_MISSING_PERSONAL_ID",
                _("Employees are missing personal identifiers"),
                _("{0} employee(s) have no value in Personal ID.").format(len(missing_ids)),
                missing_ids,
            )
        if malformed_ids:
            _add_issue(
                issues,
                "warning",
                "EMP_PERSONAL_ID_FORMAT",
                _("Personal identifiers need review"),
                _("{0} Personal ID value(s) are not 11 digits with optional cédula separators.").format(len(malformed_ids)),
                malformed_ids,
            )
    else:
        _add_issue(
            issues,
            "warning",
            "EMP_NO_PERSONAL_ID_FIELD",
            _("No personal identifier field is configured"),
            _("A dedicated employee identifier is needed for auditable DGII/TSS exports."),
        )

    nss_fields = [fieldname for fieldname in ("nss", "custom_nss", "social_security_number") if meta.has_field(fieldname)]
    if not nss_fields:
        _add_issue(
            issues,
            "warning",
            "EMP_NO_NSS_FIELD",
            _("No dedicated NSS field is configured"),
            _("The site cannot independently produce a complete TSS identity file without a dedicated NSS field."),
        )

    insurance_fields = [fieldname for fieldname in ("health_insurance_provider", "health_insurance_no") if meta.has_field(fieldname)]
    if insurance_fields:
        incomplete = [row.name for row in rows if any(not row.get(fieldname) for fieldname in insurance_fields)]
        if incomplete:
            _add_issue(
                issues,
                "warning",
                "EMP_INCOMPLETE_INSURANCE",
                _("Employee insurance data is incomplete"),
                _("{0} employee(s) are missing an insurance provider or insurance number.").format(len(incomplete)),
                incomplete,
            )

    _check_holiday_lists(entry, rows, issues)


def _check_holiday_lists(entry, employees, issues):
    if not entry.start_date or not entry.end_date:
        return

    default_holiday_list = frappe.db.get_value("Company", entry.company, "default_holiday_list")
    resolved = {row.name: row.holiday_list or default_holiday_list for row in employees}
    missing = [employee for employee, holiday_list in resolved.items() if not holiday_list]
    if missing:
        _add_issue(
            issues,
            "warning",
            "EMP_MISSING_HOLIDAY_LIST",
            _("Employees have no Holiday List"),
            _("{0} employee(s) resolve to neither an employee nor company Holiday List.").format(len(missing)),
            missing,
        )

    list_names = sorted({name for name in resolved.values() if name})
    coverage = {
        row.name: row
        for row in frappe.get_all(
            "Holiday List",
            filters={"name": ["in", list_names]},
            fields=["name", "from_date", "to_date"],
        )
    }
    expired = []
    for employee, holiday_list in resolved.items():
        dates = coverage.get(holiday_list)
        if not dates or getdate(dates.from_date) > getdate(entry.start_date) or getdate(dates.to_date) < getdate(entry.end_date):
            expired.append(f"{employee}: {holiday_list}")
    if expired:
        _add_issue(
            issues,
            "warning",
            "EMP_HOLIDAY_LIST_COVERAGE",
            _("Holiday Lists do not cover the payroll period"),
            _("{0} employee Holiday List assignment(s) do not cover the full payroll period.").format(len(expired)),
            expired,
        )


def _check_payroll_rules(entry, issues):
    tss_rule = get_tss_rule(getdate(entry.end_date))
    isr_scale = get_isr_scale(getdate(entry.end_date))
    settings = frappe.get_single("DGII Payroll Settings")
    rate_checks = (
        ("employee_afp", settings.pension_fund_provider, _("Employee AFP")),
        ("employee_ars", settings.health_insurance_rate, _("Employee ARS")),
        ("employer_infotep", settings.infotep_employer_rate, _("Employer INFOTEP")),
    )
    for key, actual, label in rate_checks:
        expected = EXPECTED_RATES[key]
        if not _rate_matches(actual, expected):
            _add_issue(
                issues,
                "blocker",
                f"RATE_{key.upper()}",
                _("{0} rate is incorrect").format(label),
                _("Configured: {0}%; expected: {1}%.").format(round(float(actual or 0), 4), expected),
            )

    srl_rate = float(settings.srl_employer_rate or 0)
    if not 1.0 <= srl_rate <= 1.6:
        _add_issue(
            issues,
            "blocker",
            "RATE_EMPLOYER_SRL",
            _("Employer SRL rate is outside the legal configuration range"),
            _("Configured: {0}%; expected a company-specific rate between 1.00% and 1.60%.").format(srl_rate),
        )
    if not settings.srl_rate_verified:
        _add_issue(
            issues,
            "blocker",
            "TSS_SRL_RATE_UNVERIFIED",
            _("SRL rate has not been verified against TSS"),
            _("Reconcile the configured {0}% rate to IGC's current TSS notification or pre-liquidation, then enable the verification checkbox.").format(srl_rate),
        )

    structures = frappe.get_all(
        "Salary Structure",
        filters={
            "docstatus": 1,
            "is_active": "Yes",
            "company": entry.company,
            "currency": entry.currency,
            "payroll_frequency": entry.payroll_frequency,
            "salary_slip_based_on_timesheet": entry.salary_slip_based_on_timesheet,
        },
        pluck="name",
    )
    for structure_name in structures:
        structure = frappe.get_doc("Salary Structure", structure_name)
        formulas = {row.salary_component: row.formula or "" for row in structure.deductions}
        expected_formulas = {
            "AFP Empleador": "base*0.0710",
            "ARS Empleador": "base*0.0709",
            "INFOTEP Empleador": "(base+COM)*(infotep_employer_rate/100)",
            "SRL Empleador": (
                "(base+COM+VACifbase+COM+VAC<=srl_ceilingelsesrl_ceiling)"
                "*(srl_employer_rate/100)"
            ),
        }
        for component, expected_formula in expected_formulas.items():
            if _normalise_formula(formulas.get(component)) != expected_formula:
                _add_issue(
                    issues,
                    "blocker",
                    f"STRUCTURE_{component.replace(' ', '_').upper()}",
                    _("Employer contribution formula is incorrect"),
                    _("{0}: {1} must use {2}.").format(structure_name, component, expected_formula),
                )

        if not any("srl" in component.lower() or "riesgo" in component.lower() for component in formulas):
            _add_issue(
                issues,
                "warning",
                "TSS_SRL_NOT_CONFIGURED",
                _("SRL employer contribution is not configured"),
                _("{0} has no occupational-risk component. The rate must come from IGC's TSS/IDOPPRIL classification.").format(structure_name),
            )

        uncapped = [
            component
            for component in ("AFP", "ARS", "AFP Empleador", "ARS Empleador")
            if component in formulas and not _formula_has_cap(formulas[component])
        ]
        if uncapped:
            _add_issue(
                issues,
                "warning",
                "TSS_CEILINGS_NOT_CONFIGURED",
                _("TSS contribution ceilings are not date-effective"),
                _(
                    "{0}: these formulas have no explicit ceiling: {1}. Applicable ceilings at {2}: "
                    "pensions {3}, health {4}, SRL {5}."
                ).format(
                    structure_name,
                    ", ".join(uncapped),
                    entry.end_date,
                    tss_rule.pension_ceiling,
                    tss_rule.sfs_ceiling,
                    tss_rule.srl_ceiling,
                ),
                uncapped,
            )

        isr_formula = formulas.get("ISR", "")
        if re.search(r"\d{6}(?:\.\d+)?", isr_formula):
            _add_issue(
                issues,
                "warning",
                "DGII_ISR_HARDCODED",
                _("ISR brackets are hard-coded"),
                _(
                    "{0} embeds annual ISR thresholds in its formula. The versioned reference for {1} "
                    "is exempt through {2}; validate the monthly taxable-base method independently."
                ).format(structure_name, entry.end_date, isr_scale.exempt_through),
            )


def _check_additional_salary(entry, employees, issues):
    if not employees or not entry.start_date or not entry.end_date:
        return
    rows = frappe.get_all(
        "Additional Salary",
        filters={
            "employee": ["in", employees],
            "payroll_date": ["between", [entry.start_date, entry.end_date]],
            "docstatus": ["<", 2],
        },
        fields=["name", "employee", "salary_component", "docstatus"],
        order_by="employee, name",
    )
    drafts = [f"{row.employee}: {row.salary_component} ({row.name})" for row in rows if row.docstatus == 0]
    submitted = [row for row in rows if row.docstatus == 1]
    if drafts:
        _add_issue(
            issues,
            "warning",
            "ADDITIONAL_SALARY_DRAFTS",
            _("Draft Additional Salary records exist"),
            _("{0} draft record(s) fall inside the period and will not be included as submitted payroll inputs.").format(len(drafts)),
            drafts,
        )
    if submitted:
        _add_issue(
            issues,
            "info",
            "ADDITIONAL_SALARY_SUBMITTED",
            _("Submitted Additional Salary inputs found"),
            _("{0} submitted record(s) fall inside this payroll period.").format(len(submitted)),
        )


def _is_dominican_id_shape(value):
    digits = re.sub(r"\D", "", value or "")
    return len(digits) == 11


def _normalise_formula(formula):
    return re.sub(r"\s+", "", formula or "")


def _formula_has_cap(formula):
    normalised = _normalise_formula(formula).lower()
    return "min(" in normalised or "ceiling" in normalised or "cap" in normalised


def _rate_matches(actual, expected):
    return abs(float(actual or 0) - float(expected or 0)) < 0.000001
