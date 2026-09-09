"""All operational writes go through the validated service, never generic CRUD."""
import frappe
from frappe.model.document import Document


class ManagedDietaDocument(Document):
    def validate(self):
        if not self.flags.get('dieta_service'):
            frappe.throw('Utilice los diálogos de Dietas.', frappe.PermissionError)

    def on_trash(self):
        frappe.throw('El historial de dietas no se puede eliminar.', frappe.PermissionError)

    def before_rename(self, *args, **kwargs):
        frappe.throw('El historial de dietas no se puede renombrar.', frappe.PermissionError)
