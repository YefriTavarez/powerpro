# Copyright (c) 2026, PowerPro contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime

from powerpro.controllers.overtime import reconcile_overtime_document
from powerpro.payroll_rules.retroactive_overtime import (
	is_adjustment_date_allowed,
	is_completed_historical_window,
	is_submission_deadline_open,
)
from powerpro.power_pro.doctype.overtime_authorization.overtime_authorization import (
	OvertimeAuthorization,
	is_assigned_approver,
)


class RetroactiveOvertimeAdjustment(OvertimeAuthorization):
	"""Audited exception for already-worked overtime supported by check-in evidence."""

	def _validate_feature_flag(self):
		if not frappe.db.get_single_value(
			"DGII Payroll Settings", "enable_overtime_authorization"
		):
			frappe.throw(
				_("Overtime Authorization is disabled in DGII Payroll Settings."),
				title=_("Feature disabled"),
			)
		if not frappe.db.get_single_value(
			"DGII Payroll Settings", "enable_retroactive_overtime_adjustment"
		):
			frappe.throw(
				_("Retroactive Overtime Adjustment is disabled in DGII Payroll Settings."),
				title=_("Feature disabled"),
			)

		deadline = frappe.db.get_single_value(
			"DGII Payroll Settings", "retroactive_overtime_submission_deadline"
		)
		if not deadline:
			frappe.throw(_("A Retroactive Overtime Submission Deadline is required."))
		if not is_submission_deadline_open(deadline, now_datetime()):
			frappe.throw(
				_("The retroactive overtime submission period closed on {0}.").format(
					frappe.bold(deadline)
				)
			)

	def _validate_window(self):
		super()._validate_window()
		if not is_completed_historical_window(
			self.authorization_end, now_datetime()
		):
			frappe.throw(
				_("A retroactive adjustment must refer only to work already completed.")
			)

		settings = frappe.get_single("DGII Payroll Settings")
		from_date = settings.retroactive_overtime_from_date
		to_date = settings.retroactive_overtime_to_date
		if not from_date or not to_date:
			frappe.throw(
				_("Retroactive Overtime From Date and To Date are required.")
			)
		if getdate(from_date) > getdate(to_date):
			frappe.throw(
				_("Retroactive Overtime From Date cannot be after To Date.")
			)
		if not is_adjustment_date_allowed(self.work_date, from_date, to_date):
			frappe.throw(
				_("Work Date must be between {0} and {1} for retroactive adjustment.").format(
					frappe.bold(from_date), frappe.bold(to_date)
				)
			)

		if not (self.exception_justification or "").strip():
			frappe.throw(_("Exception Justification is required."))

	def _validate_no_overlap(self):
		for doctype in ("Overtime Authorization", "Retroactive Overtime Adjustment"):
			if not frappe.db.exists("DocType", doctype):
				continue
			filters = [
				[doctype, "employee", "=", self.employee],
				[doctype, "docstatus", "<", 2],
				[doctype, "authorization_start", "<", self.authorization_end],
				[doctype, "authorization_end", ">", self.authorization_start],
			]
			overlaps = frappe.get_all(doctype, filters=filters, pluck="name")
			overlaps = [
				name
				for name in overlaps
				if not (doctype == self.doctype and name == self.name)
			]
			if overlaps:
				frappe.throw(
					_("This window overlaps {0} {1}.").format(
						frappe.bold(doctype), frappe.bold(overlaps[0])
					)
				)

	def before_submit(self):
		self._validate_feature_flag()
		self._validate_window()
		if not is_assigned_approver(self.approver, frappe.session.user):
			frappe.throw(
				_("Only the assigned approver {0} may submit this adjustment.").format(
					frappe.bold(self.approver)
				),
				frappe.PermissionError,
			)

		result = reconcile_overtime_document(self, include_weekly_context=True)
		if flt(result["verified_hours"]) <= 0:
			frappe.throw(
				_("No verified overtime was found inside the reviewed historical window."),
				title=_("Check-in evidence required"),
			)

		self.verified_hours = result["verified_hours"]
		self.regular_35_hours = result["regular_35_hours"]
		self.regular_100_hours = result["regular_100_hours"]
		self.holiday_100_hours = result["holiday_100_hours"]
		self.weekly_rest_hours = result["weekly_rest_hours"]
		self.night_hours = result["night_hours"]
		self.reconciliation_warnings = "\n".join(result["warnings"])
		self.reconciliation_intervals = json.dumps(
			result["intervals"], ensure_ascii=False, indent=2, sort_keys=True
		)
		self.source_checkins = json.dumps(
			result["source_checkins"], ensure_ascii=False, indent=2, sort_keys=True
		)
		self.reconciled_by = frappe.session.user
		self.reconciled_on = now_datetime()
		self.status = "Approved"
		self.approved_by = frappe.session.user
		self.approved_on = now_datetime()
