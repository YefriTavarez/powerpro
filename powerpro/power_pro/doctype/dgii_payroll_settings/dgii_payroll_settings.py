# Copyright (c) 2024, Yefri Tavarez and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt


DEFAULT_OVERTIME_CANDIDATE_KEYWORDS = "Operador\nAuxiliar\nMecánico\nElectricista\nInspector\nPrensista\nTroquelador"


class DGIIPayrollSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		dependents_rate: DF.Currency
		end_night_hours: DF.Time | None
		enable_overtime_candidate_generation: DF.Check
		enable_overtime_authorization: DF.Check
		enable_overtime_compensatory_settlement: DF.Check
		enable_overtime_settlement: DF.Check
		enable_retroactive_overtime_adjustment: DF.Check
		extra_hours_rate: DF.Percent
		extraordinary_hours_rate: DF.Percent
		health_insurance_rate: DF.Percent
		max_weekly_extra_hours: DF.Float
		night_hours_rate: DF.Percent
		overtime_candidate_designation_keywords: DF.SmallText | None
		overtime_candidate_lookback_days: DF.Int
		overtime_candidate_threshold_minutes: DF.Int
		overtime_compensatory_leave_type: DF.Link | None
		overtime_hours_per_leave_day: DF.Float
		overtime_leave_increment: DF.Float
		overtime_settlement_roles: DF.SmallText | None
		pension_fund_provider: DF.Percent
		retroactive_overtime_from_date: DF.Date | None
		retroactive_overtime_submission_deadline: DF.Date | None
		retroactive_overtime_to_date: DF.Date | None
		start_night_hours: DF.Time | None
		weekly_expected_hours: DF.Float
	# end: auto-generated types

	def validate(self):
		if self.enable_overtime_candidate_generation:
			if cint(self.overtime_candidate_threshold_minutes) <= 0:
				self.overtime_candidate_threshold_minutes = 15
			if cint(self.overtime_candidate_lookback_days) <= 0:
				self.overtime_candidate_lookback_days = 2
			if not (self.overtime_candidate_designation_keywords or "").strip():
				self.overtime_candidate_designation_keywords = (
					DEFAULT_OVERTIME_CANDIDATE_KEYWORDS
				)

		if self.enable_overtime_settlement and not (
			self.overtime_settlement_roles or ""
		).strip():
			frappe.throw(_("At least one Overtime Settlement Role is required."))

		if not self.enable_overtime_compensatory_settlement:
			return
		if not self.enable_overtime_settlement:
			frappe.throw(
				_("Enable Overtime Settlement before enabling compensatory settlement.")
			)
		if not self.overtime_compensatory_leave_type:
			frappe.throw(_("Compensatory Leave Type is required."))
		if not frappe.db.get_value(
			"Leave Type", self.overtime_compensatory_leave_type, "is_compensatory"
		):
			frappe.throw(
				_("Compensatory Leave Type must be marked as compensatory in HRMS.")
			)
		if flt(self.overtime_hours_per_leave_day) <= 0:
			frappe.throw(_("Overtime Hours per Leave Day must be greater than zero."))
		increment = flt(self.overtime_leave_increment)
		if increment <= 0 or increment > 1:
			frappe.throw(_("Leave Credit Increment must be greater than zero and at most one day."))
