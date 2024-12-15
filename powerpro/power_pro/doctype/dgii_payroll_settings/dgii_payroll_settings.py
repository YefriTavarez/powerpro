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
		extra_hours_rate: DF.Percent
		extraordinary_hours_rate: DF.Percent
		health_insurance_rate: DF.Percent
		max_weekly_extra_hours: DF.Float
		night_hours_rate: DF.Percent
		pension_fund_provider: DF.Percent
		start_night_hours: DF.Time | None
		weekly_expected_hours: DF.Float
	# end: auto-generated types
	pass
