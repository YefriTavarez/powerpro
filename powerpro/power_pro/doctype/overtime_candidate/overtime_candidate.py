# Copyright (c) 2026, PowerPro contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class OvertimeCandidate(Document):
	def before_insert(self):
		if not self.flags.generated_by_overtime_scanner:
			frappe.throw(
				_("Overtime Candidates are generated from Employee Checkin evidence."),
				frappe.PermissionError,
			)

	def validate(self):
		if self.is_new():
			return
		if not (
			self.flags.generated_by_overtime_scanner
			or self.flags.allow_candidate_decision
		):
			frappe.throw(
				_("Use the Overtime review actions to update this generated record."),
				frappe.PermissionError,
			)
