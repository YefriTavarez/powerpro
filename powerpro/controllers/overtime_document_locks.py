"""Employee mutex ordering shared by native documents and overtime services."""
import frappe
from frappe import _


def lock_employees_before_save(doc):
    """Acquire the employee mutex before Frappe locks the parent and its children."""
    stored = frappe.db.get_value(doc.doctype, doc.name, 'employee') if not doc.is_new() else None
    employees = {name for name in (stored, doc.employee) if name}
    for name in sorted(employees):
        frappe.db.get_value('Employee', name, 'name', for_update=True)
    return employees


def check_locked_employee(doc, employees):
    before = doc.get_doc_before_save()
    if before and before.employee not in employees:
        frappe.throw(_('El empleado del documento cambió; recargue antes de continuar.'))
