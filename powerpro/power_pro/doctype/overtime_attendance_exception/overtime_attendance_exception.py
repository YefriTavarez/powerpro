import frappe
from frappe.model.document import Document

class OvertimeAttendanceException(Document):
    def validate(self):
        frappe.throw("Attendance exceptions are recorded from Overtime Work Call.", frappe.PermissionError)

    def on_trash(self):
        frappe.throw("Attendance exception audit records cannot be deleted.", frappe.PermissionError)
