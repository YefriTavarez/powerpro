import frappe
from frappe import _
from frappe.model.document import Document


class OvertimeEvidenceWatch(Document):
    def validate(self):
        if not frappe.flags.get('overtime_evidence_monitor_write'):
            frappe.throw(_('La bandeja se actualiza mediante una nueva comprobación de evidencia.'),frappe.PermissionError)

    def on_trash(self):
        frappe.throw(_('Conserve el seguimiento y su historial de cambios.'),frappe.PermissionError)
