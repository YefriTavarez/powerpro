# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	import datetime

import frappe

__all__ = (
	"set_dgii_payroll_settings",
	"set_mid_month_start",
	"get_dgii_payroll_settings",
)


settings = None
def set_dgii_payroll_settings(doc):
	global settings

	if settings is None:
		settings = get_dgii_payroll_settings(doc)

	doc.update({
		"weekly_expected_hours": settings.weekly_expected_hours,
		"max_weekly_extra_hours": settings.max_weekly_extra_hours,
		"start_night_hours": settings.start_night_hours,
		"end_night_hours": settings.end_night_hours,
		"extra_hours_rate": settings.extra_hours_rate,
		"extraordinary_hours_rate": settings.extraordinary_hours_rate,
		"night_hours_rate": settings.night_hours_rate,
		"pension_fund_provider": settings.pension_fund_provider,
		"health_insurance_rate": settings.health_insurance_rate,
	})


def set_mid_month_start(doc, method=None):
	start_date: "datetime.date" = frappe.utils.getdate(doc.start_date)
	if start_date.strftime("%d") >= "15" or doc.payroll_frequency == "Monthly":
		doc.mid_month_start = True
	else:
		doc.mid_month_start = False


def get_dgii_payroll_settings(doc):
	doctype = "DGII Payroll Settings"
	return frappe.get_single(doctype)
