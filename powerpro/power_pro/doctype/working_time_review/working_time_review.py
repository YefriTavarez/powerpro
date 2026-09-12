import frappe
from frappe import _
from frappe.model.document import Document


class WorkingTimeReview(Document):
    def validate(self):
        if not frappe.flags.get('working_time_incident_write'):
            frappe.throw(_('Use las acciones de inscripción, pausa y reasignación para conservar la auditoría.'),frappe.PermissionError)

    def on_trash(self):
        frappe.throw(_('Conserve la evaluación y su historial.'),frappe.PermissionError)
