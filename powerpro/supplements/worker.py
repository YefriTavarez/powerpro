"""Queued payroll integration for the regular (non-mixed) HRMS generation path."""
import frappe
from frappe import _
from frappe.utils import getdate
from powerpro.supplements import service


def enabled_for(entry):
    config = service.settings()
    return bool(config and entry.company == config.company and entry.end_date and
                getdate(entry.end_date) >= getdate(config.effective_from))


def generate(entry, employees, args):
    """Caller owns transaction. Used by worker and rollback-only integration tests."""
    entry.check_permission("write")
    if entry.docstatus != 1 or not enabled_for(entry):
        service.fail("La nómina o la configuración cambió mientras esperaba en cola. Vuelva a generar.")
    if set(employees) != {r.employee for r in entry.employees} or any(
        str(args.get(k) or "") != str(entry.get(k) or "") for k in (
            "company", "currency", "start_date", "end_date", "payroll_frequency", "posting_date",
            "salary_slip_based_on_timesheet", "exchange_rate",
            "deduct_tax_for_unclaimed_employee_benefits", "deduct_tax_for_unsubmitted_tax_exemption_proof",
        )
    ):
        service.fail("Los empleados o parámetros de nómina cambiaron después de encolar el trabajo.")
    for employee in sorted(set(employees)):
        service.lock_employee(employee)
        existing = service.current_rows("Salary Slip", filters={"employee": employee, "docstatus": ["<", 2],
            "start_date": ["<=", entry.end_date], "end_date": [">=", entry.start_date]},
            fields=["name", "payroll_entry", "start_date", "end_date", "payroll_frequency"])
        if existing:
            if len(existing) == 1 and existing[0].payroll_entry == entry.name and all(
                getdate(existing[0][k]) == getdate(entry.get(k)) for k in ("start_date", "end_date")
            ) and existing[0].payroll_frequency == entry.payroll_frequency:
                service.validate_slip(frappe.get_doc("Salary Slip", existing[0].name))
                continue
            service.fail(f"{employee}: existe un recibo superpuesto de otra nómina o período.")
        frappe.get_doc(dict(args, doctype="Salary Slip", employee=employee)).insert()
    entry.db_set(dict(status="Submitted", salary_slips_created=1, error_message=""))


def create_slips(employees, args, publish_progress=False):
    from hrms.payroll.doctype.payroll_entry.payroll_entry import log_payroll_failure
    entry = frappe.get_doc("Payroll Entry", args["payroll_entry"])
    if entry.docstatus != 1:
        return
    try:
        generate(entry, employees, args)
    except Exception as exc:
        frappe.db.rollback()
        log_payroll_failure("creation", entry, exc)
    finally:
        frappe.db.commit()  # same boundary as HRMS, including all generated Additional Salaries
        frappe.publish_realtime("completed_salary_slip_creation", user=frappe.session.user)
