import frappe
from frappe import _
from frappe.model.document import Document


class WorkingTimeIncident(Document):
    def validate(self):
        if not frappe.flags.get('working_time_incident_write'):
            frappe.throw(_('Use las acciones de seguimiento para conservar la evidencia y la auditoría.'), frappe.PermissionError)

    def on_trash(self):
        frappe.throw(_('Conserve la incidencia y su historial de resolución.'), frappe.PermissionError)
