"""Read trusted request state; event rules live in Server Scripts."""
import frappe
from frappe.model.document import Document


class OvertimeRestWatch(Document):
    def is_service_write(self):
        # safe_exec's frappe.flags is an isolated dictionary, not the request flags.
        return bool(frappe.flags.get('overtime_rest_watch_write'))
