"""Immutable service-owned reconciliation evidence."""
import frappe
from frappe.model.document import Document

class OvertimeReconciliationRun(Document):
    def validate(self):
        frappe.throw("Las evaluaciones se crean exclusivamente desde el servicio de conciliación.")
    def on_trash(self):
        frappe.throw("Las evaluaciones forman parte de la auditoría y no se eliminan.")
