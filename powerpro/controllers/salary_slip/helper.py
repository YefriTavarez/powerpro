# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	import datetime

import frappe
from frappe import _
from frappe.query_builder.functions import Sum
from frappe.utils import flt, get_first_day

from powerpro.payroll_rules.employer_contributions import (
	DEDICATED_MODE,
	LEGACY_MODE,
	calculate_employer_contributions,
)
from powerpro.payroll_rules.dominican_republic import get_tss_rule

__all__ = (
	"set_dgii_payroll_settings",
	"set_mid_month_start",
	"get_dgii_payroll_settings",
	"populate_employer_contributions",
	"validate_employer_contributions",
)


LEGACY_EMPLOYER_COMPONENTS = {
	"Gasto AFP Empleador",
	"AFP Empleador",
	"Gasto ARS Empleador",
	"ARS Empleador",
	"Gasto INFOTEP Empleador",
	"INFOTEP Empleador",
	"Gasto SRL Empleador",
	"SRL Empleador",
}


def set_dgii_payroll_settings(doc, _=None):
	settings = get_dgii_payroll_settings(doc)
	tss_rule = get_tss_rule(doc.end_date or doc.posting_date)

	doc.update({
		"weekly_expected_hours": settings.weekly_expected_hours,
		"max_weekly_extra_hours": settings.max_weekly_extra_hours,
		"start_night_hours": settings.start_night_hours,
		"end_night_hours": settings.end_night_hours,
		"extra_hours_rate": settings.extra_hours_rate,
		"extraordinary_hours_rate": settings.extraordinary_hours_rate,
		"night_hours_rate": settings.night_hours_rate,
		"pension_fund_provider": settings.pension_fund_provider,
		"dependents_rate": settings.dependents_rate,
		"health_insurance_rate": settings.health_insurance_rate,
		"infotep_employer_rate": settings.infotep_employer_rate or 1.0,
		"srl_employer_rate": settings.srl_employer_rate or 1.2,
		"srl_ceiling": tss_rule.srl_ceiling,
	})
	if doc.meta.has_field("employer_contribution_mode") and (
		doc.is_new() or not doc.get("employer_contribution_mode")
	):
		doc.employer_contribution_mode = settings.employer_contribution_mode or LEGACY_MODE


def set_mid_month_start(doc, _=None):
	start_date: "datetime.date" = frappe.utils.getdate(doc.start_date)
	if start_date.strftime("%d") >= "15" or doc.payroll_frequency == "Monthly":
		doc.mid_month_start = True
	else:
		doc.mid_month_start = False


def get_dgii_payroll_settings(doc):
	doctype = "DGII Payroll Settings"
	return frappe.get_single(doctype)


def populate_employer_contributions(doc):
	"""Snapshot employer-only obligations without affecting employee totals."""
	if not doc.meta.has_field("employer_contributions"):
		return

	doc.set("employer_contributions", [])
	if doc.get("employer_contribution_mode") != DEDICATED_MODE or not _is_monthly_settlement(doc):
		return

	monthly_salary = _get_monthly_salary(doc)
	commissions = _get_month_component_amount(doc, "COM")
	statutory_vacation = _get_month_component_amount(doc, "VAC")
	settings = get_dgii_payroll_settings(doc)
	rows = calculate_employer_contributions(
		monthly_salary=monthly_salary,
		on_date=doc.end_date or doc.posting_date,
		commissions=commissions,
		statutory_vacation=statutory_vacation,
		infotep_rate_percent=settings.infotep_employer_rate or 1.0,
		srl_rate_percent=settings.srl_employer_rate or 1.2,
	)

	for row in rows:
		doc.append(
			"employer_contributions",
			{
				"contribution_code": row.code,
				"contribution_name": row.name,
				"base_amount": row.base_amount,
				"rate": row.rate_percent,
				"ceiling": row.ceiling,
				"amount": row.amount,
				"expense_account": row.expense_account,
				"payable_account": row.payable_account,
				"rule_effective_from": row.rule_effective_from,
			},
		)

	validate_employer_contributions(doc)


def validate_employer_contributions(doc, _event=None):
	if doc.get("employer_contribution_mode") != DEDICATED_MODE:
		return

	legacy_rows = [
		row.salary_component
		for table in ("earnings", "deductions")
		for row in doc.get(table, [])
		if row.salary_component in LEGACY_EMPLOYER_COMPONENTS and flt(row.amount)
	]
	if legacy_rows:
		frappe.throw(
			_("Dedicated employer accounting cannot be combined with legacy Salary Components: {0}").format(
				", ".join(sorted(set(legacy_rows)))
			)
		)

	if _is_monthly_settlement(doc) and len(doc.get("employer_contributions", [])) != 4:
		frappe.throw(_("Dedicated employer accounting requires exactly four contribution snapshots."))

	for row in doc.get("employer_contributions", []):
		if flt(row.amount) < 0 or not row.expense_account or not row.payable_account:
			frappe.throw(_("Employer contribution {0} has an invalid amount or account.").format(row.contribution_name))


def _is_monthly_settlement(doc):
	return bool(doc.get("mid_month_start") or doc.payroll_frequency == "Monthly")


def _get_monthly_salary(doc):
	assignment = getattr(doc, "_salary_structure_assignment", None)
	if assignment and assignment.get("base") is not None:
		return flt(assignment.base)

	return flt(
		frappe.db.get_value(
			"Salary Structure Assignment",
			{
				"employee": doc.employee,
				"salary_structure": doc.salary_structure,
				"from_date": ("<=", doc.start_date),
				"docstatus": 1,
			},
			"base",
			order_by="from_date desc",
		)
	)


def _get_month_component_amount(doc, abbreviation):
	component_names = set(
		frappe.get_all(
			"Salary Component",
			filters={"salary_component_abbr": abbreviation},
			pluck="name",
		)
	)
	current_amount = sum(
		flt(row.amount)
		for row in doc.get("earnings", [])
		if row.salary_component in component_names
	)
	if not component_names or not doc.start_date:
		return current_amount

	salary_slip = frappe.qb.DocType("Salary Slip")
	salary_detail = frappe.qb.DocType("Salary Detail")
	prior_amount = (
		frappe.qb.from_(salary_slip)
		.join(salary_detail)
		.on(salary_detail.parent == salary_slip.name)
		.select(Sum(salary_detail.amount))
		.where(
			(salary_slip.docstatus == 1)
			& (salary_slip.employee == doc.employee)
			& (salary_slip.company == doc.company)
			& (salary_slip.start_date >= get_first_day(doc.start_date))
			& (salary_slip.end_date < doc.start_date)
			& (salary_detail.parentfield == "earnings")
			& (salary_detail.salary_component.isin(component_names))
		)
	).run()[0][0]

	return current_amount + flt(prior_amount)
