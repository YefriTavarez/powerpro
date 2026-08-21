# Copyright (c) 2024, Yefri Tavarez and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class DGIIPayrollSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		dependents_rate: DF.Currency
		end_night_hours: DF.Time | None
		enable_overtime_authorization: DF.Check
		enable_retroactive_overtime_adjustment: DF.Check
		extra_hours_rate: DF.Percent
		extraordinary_hours_rate: DF.Percent
		health_insurance_rate: DF.Percent
		max_weekly_extra_hours: DF.Float
		night_hours_rate: DF.Percent
		pension_fund_provider: DF.Percent
		retroactive_overtime_from_date: DF.Date | None
		retroactive_overtime_submission_deadline: DF.Date | None
		retroactive_overtime_to_date: DF.Date | None
		start_night_hours: DF.Time | None
		weekly_expected_hours: DF.Float
	# end: auto-generated types
	pass
