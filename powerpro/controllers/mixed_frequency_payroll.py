"""Opt-in mixed payroll adapter. Monthly slips retain a full calendar month."""

from copy import copy

import frappe
from frappe import _
from frappe.utils import cint, getdate

from powerpro.payroll_rules.mixed_frequency import is_second_quincena, salary_period

SETTING = "include_monthly_in_second_quincena"


def eligible(entry):
    return is_second_quincena(
        entry.get("payroll_frequency"), entry.get("start_date"), entry.get("end_date"),
        cint(entry.get("salary_slip_based_on_timesheet")),
    )


def enabled(entry):
    return eligible(entry) and cint(frappe.get_cached_doc("DGII Payroll Settings").get(SETTING))


def frequencies(entry):
    return ["Bimonthly", "Monthly"] if enabled(entry) else [entry.get("payroll_frequency")]


def assignments(entry, employees=None):
    """Resolve newest submitted assignment before filtering its structure/frequency.

    An old eligible assignment must never resurrect a superseded contract.
    """
    filters = {
        "docstatus": 1, "company": entry.company, "currency": entry.currency,
        "from_date": ["<=", entry.end_date],
    }
    if employees is not None:
        if not employees:
            return {}
        filters["employee"] = ["in", list(employees)]
    rows = frappe.get_all(
        "Salary Structure Assignment", filters=filters,
        fields=["name", "employee", "salary_structure", "from_date", "payroll_payable_account"],
        order_by="from_date desc, creation desc, name desc",
    )
    latest = {}
    for row in rows:
        latest.setdefault(row.employee, row)
    allowed = frappe.get_all(
        "Salary Structure", filters={
            "docstatus": 1, "is_active": "Yes", "company": entry.company,
            "currency": entry.currency, "salary_slip_based_on_timesheet": 0,
            "payroll_frequency": ["in", ["Monthly", "Bimonthly"]],
        }, fields=["name", "payroll_frequency"],
    )
    structures = {row.name: row.payroll_frequency for row in allowed}
    result = {}
    for employee, row in latest.items():
        if row.salary_structure not in structures or row.payroll_payable_account != entry.payroll_payable_account:
            continue
        row.update(salary_period(structures[row.salary_structure], entry.start_date, entry.end_date))
        result[employee] = row
    return result


def require_assignment(entry, employee):
    assignment = assignments(entry, [employee]).get(employee)
    if not assignment:
        frappe.throw(_("Employee {0} has no current assignment eligible for this mixed payroll.").format(employee))
    return assignment


def overlaps(entry, employee, period, exclude=None):
    filters = {
        "company": entry.company, "employee": employee, "docstatus": ["<", 2],
        "start_date": ["<=", period.end_date], "end_date": [">=", period.start_date],
    }
    if exclude:
        filters["name"] = ["!=", exclude]
    return frappe.get_all(
        "Salary Slip", filters=filters,
        fields=["name", "employee", "payroll_entry", "start_date", "end_date", "docstatus",
                "payroll_frequency", "salary_structure"],
    )


def employee_list(filters, searchfield=None, search_string=None, fields=None, as_dict=True,
                  limit=None, offset=None, ignore_match_conditions=False):
    from powerpro.controllers.payroll_entry import get_filtered_employees, get_salary_structure

    resolved = assignments(filters)
    candidates = {}
    for frequency in ("Bimonthly", "Monthly"):
        scoped = frappe._dict(filters.copy())
        scoped.update(salary_period(frequency, filters.start_date, filters.end_date))
        structures = get_salary_structure(filters.company, filters.currency, 0, frequency)
        if not structures:
            continue
        # Apply paging only after resolving current assignments and excluding paid periods.
        rows = get_filtered_employees(
            structures, scoped, searchfield, search_string, fields, as_dict=as_dict,
            ignore_match_conditions=ignore_match_conditions,
        )
        for row in rows:
            employee = row.employee if as_dict else row[0]
            period = resolved.get(employee)
            if not period or period.payroll_frequency != frequency:
                continue
            if overlaps(filters, employee, period):
                continue
            candidates[employee] = row
    rows = list(candidates.values())
    start = cint(offset)
    return rows[start:start + cint(limit)] if limit else rows[start:]


def prepare_slip(slip):
    """Called before working-day calculation and validation, also by preview."""
    slip._pp_mixed_assignment = None
    if not slip.is_new() or not slip.payroll_entry or not slip.employee:
        return
    entry = frappe.get_cached_doc("Payroll Entry", slip.payroll_entry)
    if not enabled(entry):
        return
    if slip.employee not in {row.employee for row in entry.employees}:
        frappe.throw(_("Employee is not selected in the linked Payroll Entry."))
    period = require_assignment(entry, slip.employee)
    slip.update({key: period[key] for key in ("payroll_frequency", "start_date", "end_date")})
    slip.salary_structure = period.salary_structure
    slip._pp_mixed_assignment = period


def validate_slip(slip):
    if not slip.payroll_entry or not slip.employee:
        return
    entry = frappe.get_cached_doc("Payroll Entry", slip.payroll_entry)
    # Retain duplicate protection after the option is disabled for future runs.
    if not eligible(entry) or not (enabled(entry) or slip.payroll_frequency == "Monthly"):
        return
    from powerpro.controllers.salary_slip.monthly import lock_employee
    lock_employee(slip)
    period = frappe._dict(salary_period(slip.payroll_frequency, entry.start_date, entry.end_date))
    if getdate(slip.start_date) != period.start_date or getdate(slip.end_date) != period.end_date:
        frappe.throw(_("Salary Slip dates do not match its frequency in the mixed Payroll Entry."))
    if overlaps(entry, slip.employee, period, exclude=slip.name):
        frappe.throw(_("Employee {0} already has an overlapping Salary Slip.").format(slip.employee))


def read_scope(entry):
    """Extend only linked-slip reads; do not change the saved Payroll Entry dates.

    Existing monthly slips must remain available for accrual/payment after disabling
    the setting. Parent HRMS methods retain their payroll_entry and status filters.
    """
    if eligible(entry) and frappe.db.exists("Salary Slip", {
        "payroll_entry": entry.name, "payroll_frequency": "Monthly", "docstatus": ["<", 2],
        "start_date": getdate(entry.end_date).replace(day=1), "end_date": entry.end_date,
    }):
        scoped = copy(entry)
        scoped.start_date = getdate(entry.end_date).replace(day=1)
        return scoped
    return entry


def attendance(entry, parent):
    if not enabled(entry):
        return parent(entry).get_employees_with_unmarked_attendance()
    result = []
    resolved = assignments(entry, [row.employee for row in entry.employees])
    for frequency in ("Bimonthly", "Monthly"):
        scoped = copy(entry)
        scoped.employees = [row for row in entry.employees
                            if resolved.get(row.employee, {}).get("payroll_frequency") == frequency]
        if scoped.employees:
            scoped.update(salary_period(frequency, entry.start_date, entry.end_date))
            result.extend(parent(scoped).get_employees_with_unmarked_attendance() or [])
    return result


def create_slips(employees, args, publish_progress=False):
    """Single transaction and completion event for both employee groups."""
    from hrms.payroll.doctype.payroll_entry.payroll_entry import log_payroll_failure
    from powerpro.controllers.salary_slip.monthly import lock_employee

    entry = frappe.get_doc("Payroll Entry", args["payroll_entry"])
    # A cancelled entry must not be changed to Failed by a delayed queue job.
    if entry.docstatus != 1:
        return
    try:
        entry.check_permission("write")
        if not enabled(entry):
            frappe.throw(_("Mixed payroll is no longer enabled. Refresh the employee list before retrying."))
        if any(str(args.get(key) or "") != str(entry.get(key) or "") for key in (
            "company", "currency", "payroll_frequency", "start_date", "end_date", "posting_date",
            "salary_slip_based_on_timesheet", "exchange_rate",
        )):
            frappe.throw(_("Payroll settings changed after generation was queued. Please retry."))
        employees = sorted(set(employees))
        if set(employees) != {row.employee for row in entry.employees}:
            frappe.throw(_("Payroll employees changed after generation was queued. Please retry."))
        for employee in employees:
            lock_employee(frappe._dict(employee=employee))
            period = require_assignment(entry, employee)
            existing = overlaps(entry, employee, period)
            if existing:
                if len(existing) == 1 and existing[0].payroll_entry == entry.name and all(
                    getdate(existing[0][field]) == period[field] for field in ("start_date", "end_date")
                ) and existing[0].payroll_frequency == period.payroll_frequency and existing[0].salary_structure == period.salary_structure:
                    continue
                frappe.throw(_("Employee {0} already has an overlapping Salary Slip.").format(employee))
            values = dict(args, doctype="Salary Slip", employee=employee)
            values.update({key: period[key] for key in ("payroll_frequency", "start_date", "end_date")})
            frappe.get_doc(values).insert()
        entry.db_set({"status": "Submitted", "salary_slips_created": 1, "error_message": ""})
    except Exception as exc:
        frappe.db.rollback()
        log_payroll_failure("creation", entry, exc)
    finally:
        frappe.db.commit()  # same transaction boundary as the HRMS payroll worker
        frappe.publish_realtime("completed_salary_slip_creation", user=frappe.session.user)
