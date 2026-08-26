# Copyright (c) 2024, Yefri Tavarez and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils import cint


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
		enable_retroactive_overtime_adjustment: DF.Check
		extra_hours_rate: DF.Percent
		extraordinary_hours_rate: DF.Percent
		health_insurance_rate: DF.Percent
		max_weekly_extra_hours: DF.Float
		night_hours_rate: DF.Percent
		overtime_candidate_designation_keywords: DF.SmallText | None
		overtime_candidate_lookback_days: DF.Int
		overtime_candidate_threshold_minutes: DF.Int
		pension_fund_provider: DF.Percent
		retroactive_overtime_from_date: DF.Date | None
		retroactive_overtime_submission_deadline: DF.Date | None
		retroactive_overtime_to_date: DF.Date | None
		start_night_hours: DF.Time | None
		weekly_expected_hours: DF.Float
	# end: auto-generated types

	def validate(self):
		if not self.enable_overtime_candidate_generation:
			return
		if cint(self.overtime_candidate_threshold_minutes) <= 0:
			self.overtime_candidate_threshold_minutes = 15
		if cint(self.overtime_candidate_lookback_days) <= 0:
			self.overtime_candidate_lookback_days = 2
		if not (self.overtime_candidate_designation_keywords or "").strip():
			self.overtime_candidate_designation_keywords = (
				DEFAULT_OVERTIME_CANDIDATE_KEYWORDS
			)
