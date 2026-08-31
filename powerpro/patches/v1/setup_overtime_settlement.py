# Copyright (c) 2026, PowerPro contributors
# For license information, please see license.txt

"""Install non-activating metadata for audited overtime settlement."""

import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def preview():
	meta = frappe.get_meta("Leave Allocation")
	return {
		"settlement_enabled": bool(
			frappe.db.get_single_value(
				"DGII Payroll Settings", "enable_overtime_settlement"
			)
		),
		"compensatory_settlement_enabled": bool(
			frappe.db.get_single_value(
				"DGII Payroll Settings", "enable_overtime_compensatory_settlement"
			)
		),
		"leave_allocation_fields": {
			fieldname: meta.has_field(fieldname)
			for fieldname in (
				"powerpro_overtime_managed",
				"powerpro_overtime_leave_period",
			)
		},
		"managed_allocations": (
			frappe.db.count("Leave Allocation", {"powerpro_overtime_managed": 1})
			if meta.has_field("powerpro_overtime_managed")
			else 0
		),
	}


def execute():
	create_custom_fields(
		{
			"Leave Allocation": [
				{
					"fieldname": "powerpro_overtime_section",
					"label": "PowerPro Overtime",
					"fieldtype": "Section Break",
					"insert_after": "to_date",
					"read_only": 1,
				},
				{
					"fieldname": "powerpro_overtime_managed",
					"label": "System-managed Overtime Allocation",
					"fieldtype": "Check",
					"default": "0",
					"insert_after": "powerpro_overtime_section",
					"read_only": 1,
					"allow_on_submit": 1,
				},
				{
					"fieldname": "powerpro_overtime_leave_period",
					"label": "Overtime Leave Period",
					"fieldtype": "Link",
					"options": "Leave Period",
					"insert_after": "powerpro_overtime_managed",
					"read_only": 1,
					"allow_on_submit": 1,
				},
			],
		},
		ignore_validate=True,
		update=True,
	)
	frappe.clear_cache(doctype="Leave Allocation")
	print("[setup_overtime_settlement] " + json.dumps(preview(), sort_keys=True))


def disable():
	"""Emergency rollback: stop new settlement while preserving every audit record."""
	frappe.db.set_single_value("DGII Payroll Settings", "enable_overtime_settlement", 0)
	frappe.db.set_single_value(
		"DGII Payroll Settings", "enable_overtime_compensatory_settlement", 0
	)
	frappe.clear_cache(doctype="DGII Payroll Settings")
	print("[setup_overtime_settlement] Settlement disabled; records preserved.")
