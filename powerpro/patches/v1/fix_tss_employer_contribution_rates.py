# Copyright (c) 2026, Yefri Tavarez and Contributors
# For license information, please see license.txt

"""Correct the employer AFP/SFS percentages used by Dominican payroll.

The employee percentages remain unchanged. This patch updates only the two
employer Salary Components and their existing Salary Structure deduction rows.
It does not recalculate or backfill any Salary Slip.
"""

import frappe


FORMULAS = {
	"AFP Empleador": "base * 0.0710",
	"ARS Empleador": "base * 0.0709",
}

ROLLBACK_FORMULAS = {
	"AFP Empleador": "base * 0.0709",
	"ARS Empleador": "base * 0.0710",
}


def execute():
	_apply(FORMULAS)


def rollback():
	_apply(ROLLBACK_FORMULAS)


def _apply(formulas):
	for component_name, formula in formulas.items():
		_update_salary_component(component_name, formula)
		_update_salary_structure_rows(component_name, formula)


def _update_salary_component(component_name, formula):
	if not frappe.db.exists("Salary Component", component_name):
		print(f"[fix_tss_employer_contribution_rates] Missing Salary Component: {component_name}")
		return

	doc = frappe.get_doc("Salary Component", component_name)
	values = {
		"amount_based_on_formula": 1,
		"formula": formula,
		"variable_based_on_taxable_salary": 0,
		"statistical_component": 0,
		"do_not_include_in_total": 1,
	}
	if all(doc.get(fieldname) == value for fieldname, value in values.items()):
		print(f"[fix_tss_employer_contribution_rates] {component_name}: component already correct.")
		return

	doc.update(values)
	doc.flags.ignore_permissions = True
	doc.save()


def _update_salary_structure_rows(component_name, formula):
	rows = frappe.get_all(
		"Salary Detail",
		filters={
			"parenttype": "Salary Structure",
			"parentfield": "deductions",
			"salary_component": component_name,
		},
		fields=[
			"name", "amount_based_on_formula", "formula",
			"variable_based_on_taxable_salary", "do_not_include_in_total",
		],
	)

	values = {
		"amount_based_on_formula": 1,
		"formula": formula,
		"variable_based_on_taxable_salary": 0,
		"do_not_include_in_total": 1,
	}
	updated = 0
	for row in rows:
		if all(row.get(fieldname) == value for fieldname, value in values.items()):
			continue
		frappe.db.set_value(
			"Salary Detail",
			row.name,
			values,
			update_modified=False,
		)
		updated += 1

	print(
		f"[fix_tss_employer_contribution_rates] {component_name}: "
		f"updated {updated} of {len(rows)} Salary Structure row(s)."
	)
