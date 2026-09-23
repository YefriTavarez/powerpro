import frappe
from frappe import _
from frappe.model.document import Document


class OvertimeRestWatch(Document):
    def validate(self):
        if not frappe.flags.get('overtime_rest_watch_write'):
            frappe.throw(_('Use las acciones de seguimiento de descanso.'),frappe.PermissionError)

    def on_trash(self):
        frappe.throw(_('Conserve el seguimiento del descanso y su historial.'),frappe.PermissionError)
