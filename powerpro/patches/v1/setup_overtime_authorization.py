# Copyright (c) 2026, PowerPro contributors
# For license information, please see license.txt

"""Install guarded Employee metadata for pre-approved overtime.

The patch is intentionally non-activating: the feature flag and every employee
eligibility flag remain false. It does not change payroll or historical data.
"""

import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


FIELDS = (
	"overtime_authorization_section",
	"overtime_eligible",
	"overtime_approver",
)


def preview():
	settings_meta = frappe.get_meta("DGII Payroll Settings")
	return {
		"feature_enabled": bool(
			frappe.db.get_single_value(
				"DGII Payroll Settings", "enable_overtime_authorization"
			)
		),
		"retroactive_adjustment_enabled": bool(
			frappe.db.get_single_value(
				"DGII Payroll Settings", "enable_retroactive_overtime_adjustment"
			)
		)
		if settings_meta.has_field("enable_retroactive_overtime_adjustment")
		else False,
		"employee_fields": {
			fieldname: bool(
				frappe.db.exists(
					"Custom Field", {"dt": "Employee", "fieldname": fieldname}
				)
			)
			for fieldname in FIELDS
		},
		"eligible_employees": frappe.db.count(
			"Employee", {"overtime_eligible": 1}
		)
		if frappe.get_meta("Employee").has_field("overtime_eligible")
		else 0,
		"historical_records_changed": 0,
	}


def execute():
	create_custom_fields(
		{
			"Employee": [
				{
					"fieldname": "overtime_authorization_section",
					"label": "Overtime Authorization",
					"fieldtype": "Section Break",
					"insert_after": "holiday_list",
				},
				{
					"fieldname": "overtime_eligible",
					"label": "Overtime Eligible",
					"fieldtype": "Check",
					"default": "0",
					"insert_after": "overtime_authorization_section",
				},
				{
					"fieldname": "overtime_approver",
					"label": "Overtime Approver",
					"fieldtype": "Link",
					"options": "User",
					"insert_after": "overtime_eligible",
					"depends_on": "eval:doc.overtime_eligible",
					"mandatory_depends_on": "eval:doc.overtime_eligible",
				},
			],
		},
		ignore_validate=True,
		update=True,
	)
	frappe.clear_cache(doctype="Employee")
	print("[setup_overtime_authorization] " + json.dumps(preview(), sort_keys=True))


def disable():
	"""Emergency rollback: stop new authorizations without deleting audit data."""
	frappe.db.set_single_value(
		"DGII Payroll Settings", "enable_overtime_authorization", 0
	)
	if frappe.get_meta("DGII Payroll Settings").has_field(
		"enable_retroactive_overtime_adjustment"
	):
		frappe.db.set_single_value(
			"DGII Payroll Settings", "enable_retroactive_overtime_adjustment", 0
		)
	frappe.clear_cache(doctype="DGII Payroll Settings")
	print("[setup_overtime_authorization] Feature disabled; records preserved.")
