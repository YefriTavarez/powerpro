# Copyright (c) 2026, PowerPro contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class OvertimeCompensatoryCredit(Document):
	def validate(self):
		if self.is_new() and not self.flags.get("generated_from_overtime_settlement"):
			frappe.throw(
				_("Compensatory credits can only be created from an overtime settlement."),
				frappe.PermissionError,
			)
		if flt(self.banked_hours) <= 0:
			frappe.throw(_("Banked Hours must be greater than zero."))
		if flt(self.hours_per_day) <= 0:
			frappe.throw(_("Hours per Leave Day must be greater than zero."))
		if flt(self.leave_increment) <= 0:
			frappe.throw(_("Leave Increment must be greater than zero."))

	def before_submit(self):
		if not self.flags.get("generated_from_overtime_settlement"):
			frappe.throw(
				_("Compensatory credits can only be submitted by overtime settlement."),
				frappe.PermissionError,
			)
		self.status = "Credited"

	def before_cancel(self):
		if not self.flags.get("reversed_from_overtime_settlement"):
			frappe.throw(
				_("Cancel the linked Overtime Authorization instead."),
				frappe.PermissionError,
			)

	def on_cancel(self):
		self.db_set("status", "Cancelled", update_modified=False)

