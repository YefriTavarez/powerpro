# Copyright (c) 2026, PowerPro contributors
# For license information, please see license.txt

"""Add the reversible, feature-gated employer contribution accounting mode."""

import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from powerpro.patches.v1.setup_igc_employer_contributions import COMPONENTS, SALARY_STRUCTURE
from powerpro.payroll_rules.employer_contributions import DEDICATED_MODE, LEGACY_MODE


LEGACY_CONDITION = 'mid_month_start or payroll_frequency == "Monthly"'
GATED_LEGACY_CONDITION = (
	'employer_contribution_mode != "Dedicated Journal Entries" '
	'and (mid_month_start or payroll_frequency == "Monthly")'
)


def preview():
	return {
		"settings_mode": frappe.db.get_single_value(
			"DGII Payroll Settings", "employer_contribution_mode"
		),
		"salary_slip_fields": {
			fieldname: frappe.db.exists("Custom Field", {"dt": "Salary Slip", "fieldname": fieldname})
			for fieldname in (
				"employer_contribution_mode",
				"employer_contributions_tab",
				"employer_contributions",
			)
		},
		"legacy_conditions": _condition_state(),
		"submitted_salary_slips_changed": 0,
	}


def execute():
	_create_salary_slip_fields()
	settings = frappe.get_single("DGII Payroll Settings")
	if not settings.employer_contribution_mode:
		settings.employer_contribution_mode = LEGACY_MODE
		settings.save(ignore_permissions=True)

	_set_legacy_conditions(GATED_LEGACY_CONDITION)
	frappe.clear_cache(doctype="Salary Slip")
	frappe.clear_cache(doctype="Salary Structure")
	frappe.clear_cache(doctype="Salary Component")
	print(
		"[setup_dedicated_employer_contribution_journal] "
		+ json.dumps(preview(), default=str, sort_keys=True)
	)


def rollback():
	"""Return future payroll generation to component pairs; preserve snapshots."""
	settings = frappe.get_single("DGII Payroll Settings")
	settings.employer_contribution_mode = LEGACY_MODE
	settings.save(ignore_permissions=True)
	_set_legacy_conditions(LEGACY_CONDITION)
	frappe.clear_cache(doctype="Salary Slip")
	frappe.clear_cache(doctype="Salary Structure")
	frappe.clear_cache(doctype="Salary Component")
	print("[setup_dedicated_employer_contribution_journal] Legacy mode restored.")


def enable_dedicated_mode():
	"""Explicit cutover used only after DEV validation."""
	settings = frappe.get_single("DGII Payroll Settings")
	settings.employer_contribution_mode = DEDICATED_MODE
	settings.save(ignore_permissions=True)
	frappe.clear_cache(doctype="DGII Payroll Settings")
	print("[setup_dedicated_employer_contribution_journal] Dedicated mode enabled.")


def _create_salary_slip_fields():
	create_custom_fields(
		{
			"Salary Slip": [
				{
					"fieldname": "employer_contribution_mode",
					"label": "Employer Contribution Accounting Mode",
					"fieldtype": "Select",
					"options": f"{LEGACY_MODE}\n{DEDICATED_MODE}",
					"insert_after": "srl_ceiling",
					"read_only": 1,
					"hidden": 1,
				},
				{
					"fieldname": "employer_contributions_tab",
					"label": "Aportes del empleador",
					"fieldtype": "Tab Break",
					"insert_after": "tab_8",
					"depends_on": f'eval:doc.employer_contribution_mode=="{DEDICATED_MODE}"',
					"read_only": 1,
				},
				{
					"fieldname": "employer_contributions",
					"label": "Aportes del empleador",
					"fieldtype": "Table",
					"options": "Employer Contribution Detail",
					"insert_after": "employer_contributions_tab",
					"read_only": 1,
					"allow_on_submit": 0,
				},
			],
		},
		ignore_validate=True,
		update=True,
	)


def _set_legacy_conditions(condition):
	component_names = {spec["name"] for spec in COMPONENTS}
	for name in component_names:
		if frappe.db.exists("Salary Component", name):
			doc = frappe.get_doc("Salary Component", name)
			if doc.condition != condition:
				doc.condition = condition
				doc.save(ignore_permissions=True)

	structure = frappe.get_doc("Salary Structure", SALARY_STRUCTURE)
	changed = False
	for table in ("earnings", "deductions"):
		for row in structure.get(table):
			if row.salary_component in component_names and row.condition != condition:
				row.condition = condition
				changed = True
	if changed:
		structure.flags.ignore_validate_update_after_submit = True
		structure.save(ignore_permissions=True)


def _condition_state():
	component_names = {spec["name"] for spec in COMPONENTS}
	return frappe.get_all(
		"Salary Component",
		filters={"name": ["in", component_names]},
		fields=["name", "condition"],
		order_by="name",
	)
