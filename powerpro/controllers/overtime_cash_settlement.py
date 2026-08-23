# Copyright (c) 2026, PowerPro contributors
# For license information, please see license.txt

"""Audited payroll settlement for approved retroactive overtime."""

import json

import frappe
from frappe import _
from frappe.utils import flt, now_datetime

from powerpro.payroll_rules.overtime_cash_settlement import (
	calculate_cash_settlement,
)


CASH = "Cash"
SETTLEMENT_NOT_APPLICABLE = "Not Applicable"
SETTLEMENT_CREATED = "Created"
SETTLEMENT_PAID = "Paid"
SETTLEMENT_CANCELLED = "Cancelled"


def build_cash_settlement(adjustment, reconciliation):
	"""Build a read-only cash preview from an approved-style snapshot."""
	assignment = _get_effective_salary_assignment(adjustment)
	hourly_rate = _get_hourly_rate(assignment)
	rates = reconciliation.get("rates") or _get_overtime_rates()
	settlement = calculate_cash_settlement(
		hourly_rate=hourly_rate,
		regular_35_hours=reconciliation.get("regular_35_hours"),
		regular_100_hours=reconciliation.get("regular_100_hours"),
		holiday_100_hours=reconciliation.get("holiday_100_hours"),
		weekly_rest_hours=reconciliation.get("weekly_rest_hours"),
		night_hours=reconciliation.get("night_hours"),
		regular_overtime_percent=rates.get("regular_overtime_percent"),
		extraordinary_overtime_percent=rates.get("extraordinary_overtime_percent"),
		night_hours_percent=rates.get("night_hours_percent"),
	)
	settlement.update({
		"salary_structure_assignment": assignment.name,
		"currency": _get_company_currency(adjustment.company),
		"payroll_date": str(adjustment.work_date),
	})
	return settlement


def prepare_cash_settlement(adjustment, reconciliation):
	"""Validate and freeze the settlement before the adjustment is submitted."""
	if adjustment.planned_settlement != CASH:
		adjustment.settlement_status = SETTLEMENT_NOT_APPLICABLE
		adjustment.settlement_hourly_rate = 0
		adjustment.settlement_amount = 0
		adjustment.settlement_currency = None
		adjustment.settlement_breakdown = None
		adjustment.settlement_references = None
		return None

	settlement = build_cash_settlement(adjustment, reconciliation)
	_validate_cash_settlement(settlement)
	created = _create_additional_salaries(adjustment, settlement)
	settlement["additional_salaries"] = created

	adjustment.settlement_status = SETTLEMENT_CREATED
	adjustment.settlement_hourly_rate = settlement["hourly_rate"]
	adjustment.settlement_amount = settlement["total_amount"]
	adjustment.settlement_currency = settlement["currency"]
	adjustment.settlement_breakdown = json.dumps(
		settlement, ensure_ascii=False, indent=2, sort_keys=True
	)
	adjustment.settlement_references = json.dumps(created, ensure_ascii=False, indent=2)
	adjustment.settlement_created_by = frappe.session.user
	adjustment.settlement_created_on = now_datetime()
	return settlement


@frappe.whitelist()
def create_cash_settlement(adjustment):
	"""Explicitly settle a valid pre-release approved adjustment once."""
	doc = frappe.get_doc("Retroactive Overtime Adjustment", adjustment)
	if not frappe.has_permission(doc.doctype, "submit", doc=doc):
		frappe.throw(_("Not permitted to settle this overtime adjustment."), frappe.PermissionError)
	if doc.approver != frappe.session.user:
		frappe.throw(
			_("Only the assigned approver {0} may create this cash settlement.").format(
				frappe.bold(doc.approver)
			),
			frappe.PermissionError,
		)
	if doc.docstatus != 1 or doc.status != "Approved":
		frappe.throw(_("Only an approved overtime adjustment can be settled."))
	if doc.planned_settlement != CASH:
		frappe.throw(_("Only a Cash overtime adjustment creates payroll earnings."))
	if doc.settlement_status in {SETTLEMENT_CREATED, SETTLEMENT_PAID}:
		frappe.throw(
			_("Cash settlement already exists for this overtime adjustment."),
			title=_("Duplicate settlement blocked"),
		)

	# Re-run current guardrails before allowing an older submitted record to
	# enter payroll. This intentionally rejects legacy multi-day snapshots.
	doc._validate_window()
	reconciliation = {
		"regular_35_hours": doc.regular_35_hours,
		"regular_100_hours": doc.regular_100_hours,
		"holiday_100_hours": doc.holiday_100_hours,
		"weekly_rest_hours": doc.weekly_rest_hours,
		"night_hours": doc.night_hours,
		"rates": _get_overtime_rates(),
	}
	settlement = build_cash_settlement(doc, reconciliation)
	_validate_cash_settlement(settlement)
	created = _create_additional_salaries(doc, settlement)
	settlement["additional_salaries"] = created
	values = {
		"settlement_status": SETTLEMENT_CREATED,
		"settlement_hourly_rate": settlement["hourly_rate"],
		"settlement_amount": settlement["total_amount"],
		"settlement_currency": settlement["currency"],
		"settlement_breakdown": json.dumps(
			settlement, ensure_ascii=False, indent=2, sort_keys=True
		),
		"settlement_references": json.dumps(created, ensure_ascii=False, indent=2),
		"settlement_created_by": frappe.session.user,
		"settlement_created_on": now_datetime(),
	}
	frappe.db.set_value(doc.doctype, doc.name, values)
	doc.add_comment(
		"Info",
		_("Cash settlement created through Additional Salary: {0}").format(
			", ".join(created)
		),
	)
	return {**settlement, "settlement_status": SETTLEMENT_CREATED}


def before_cancel_adjustment(adjustment):
	references = _get_linked_additional_salaries(adjustment.name, docstatus=1)
	paid_slips = _get_submitted_salary_slips(references)
	if not paid_slips and adjustment.get("settlement_status") != SETTLEMENT_PAID:
		return
	salary_slip = paid_slips[0] if paid_slips else adjustment.get("settlement_salary_slip")
	frappe.throw(
		_(
			"Cancel Salary Slip {0} before cancelling this paid overtime adjustment."
		).format(frappe.bold(salary_slip)),
		title=_("Paid settlement cannot be cancelled"),
	)


def cancel_cash_settlement(adjustment):
	"""Cancel linked payroll inputs after the adjustment itself is cancelled."""
	references = _get_linked_additional_salaries(adjustment.name, docstatus=1)
	for name in references:
		doc = frappe.get_doc("Additional Salary", name)
		doc.flags.ignore_permissions = True
		doc.cancel()

	frappe.db.set_value(
		adjustment.doctype,
		adjustment.name,
		{
			"status": "Cancelled",
			"settlement_status": (
				SETTLEMENT_CANCELLED if references else adjustment.get("settlement_status")
			),
			"settlement_salary_slip": None,
		},
	)


def prevent_direct_overtime_salary_cancel(additional_salary, method=None):
	"""Keep the adjustment as the authoritative rollback entry point."""
	if additional_salary.ref_doctype != "Retroactive Overtime Adjustment":
		return
	if not additional_salary.ref_docname:
		return
	if frappe.db.get_value(
		"Retroactive Overtime Adjustment",
		additional_salary.ref_docname,
		"docstatus",
	) == 1:
		frappe.throw(
			_("Cancel the linked Retroactive Overtime Adjustment instead."),
			title=_("Overtime settlement is controlled by its adjustment"),
		)


def sync_adjustments_from_salary_slip(salary_slip, *, paid):
	additional_salary_names = {
		row.additional_salary
		for row in (salary_slip.get("earnings") or [])
		if row.additional_salary
	}
	if not additional_salary_names:
		return

	links = frappe.get_all(
		"Additional Salary",
		filters={
			"name": ["in", list(additional_salary_names)],
			"ref_doctype": "Retroactive Overtime Adjustment",
			"docstatus": 1,
		},
		fields=["name", "ref_docname"],
	)
	for adjustment_name in {row.ref_docname for row in links if row.ref_docname}:
		active_references = set(
			_get_linked_additional_salaries(adjustment_name, docstatus=1)
		)
		if paid and not active_references.issubset(additional_salary_names):
			continue
		frappe.db.set_value(
			"Retroactive Overtime Adjustment",
			adjustment_name,
			{
				"settlement_status": SETTLEMENT_PAID if paid else SETTLEMENT_CREATED,
				"settlement_salary_slip": salary_slip.name if paid else None,
			},
		)


def _create_additional_salaries(adjustment, settlement):
	# Serialize retries and simultaneous requests on the source adjustment. The
	# reference lookup below then serves as the idempotency check.
	frappe.db.get_value(adjustment.doctype, adjustment.name, "name", for_update=True)
	existing = _get_linked_additional_salaries(adjustment.name, docstatus=["<", 2])
	if existing:
		frappe.throw(
			_("Additional Salary already exists for this adjustment: {0}").format(
				frappe.bold(", ".join(existing))
			),
			title=_("Duplicate settlement blocked"),
		)

	created = []
	for line in settlement["lines"]:
		_validate_salary_component(line["component"])
		doc = frappe.new_doc("Additional Salary")
		doc.update({
			"employee": adjustment.employee,
			"company": adjustment.company,
			"currency": settlement["currency"],
			"salary_component": line["component"],
			"type": "Earning",
			"amount": line["amount"],
			"payroll_date": settlement["payroll_date"],
			"is_recurring": 0,
			"overwrite_salary_structure_amount": 0,
			"ref_doctype": adjustment.doctype,
			"ref_docname": adjustment.name,
		})
		doc.flags.ignore_permissions = True
		doc.insert()
		doc.submit()
		created.append(doc.name)
	return created


def _validate_cash_settlement(settlement):
	weekly_rest_hours = flt(settlement.get("unsettled_weekly_rest_hours"))
	if weekly_rest_hours:
		frappe.throw(
			_(
				"{0} ordinary weekly-rest hours cannot be paid automatically as overtime. "
				"Choose Compensatory Rest or correct the workday classification."
			).format(frappe.bold(weekly_rest_hours)),
			title=_("Weekly-rest settlement requires review"),
		)
	if not settlement.get("lines") or flt(settlement.get("total_amount")) <= 0:
		frappe.throw(_("The approved snapshot does not produce a cash overtime earning."))


def _get_effective_salary_assignment(adjustment):
	fields = ["name", "base"]
	meta = frappe.get_meta("Salary Structure Assignment")
	if meta.has_field("salary_per_hour"):
		fields.append("salary_per_hour")
	assignments = frappe.get_all(
		"Salary Structure Assignment",
		filters={
			"employee": adjustment.employee,
			"company": adjustment.company,
			"docstatus": 1,
			"from_date": ["<=", adjustment.work_date],
		},
		fields=fields,
		order_by="from_date desc, creation desc",
		limit=1,
	)
	if not assignments:
		frappe.throw(
			_("No submitted Salary Structure Assignment covers {0}.").format(
				frappe.bold(adjustment.work_date)
			)
		)
	return assignments[0]


def _get_hourly_rate(assignment):
	rate = flt(assignment.get("salary_per_hour"))
	if rate <= 0 and flt(assignment.get("base")) > 0:
		# Mirrors the existing Salary Structure Assignment controller for legacy
		# assignments created before the custom hourly-rate field was populated.
		rate = round(flt(assignment.base) / 23.83 / 8, 2)
	if rate <= 0:
		frappe.throw(
			_("Salary Structure Assignment {0} has no valid hourly rate.").format(
				frappe.bold(assignment.name)
			)
		)
	return rate


def _get_overtime_rates():
	settings = frappe.get_single("DGII Payroll Settings")
	return {
		"regular_overtime_percent": flt(settings.extra_hours_rate),
		"extraordinary_overtime_percent": flt(settings.extraordinary_hours_rate),
		"night_hours_percent": flt(settings.night_hours_rate),
	}


def _get_company_currency(company):
	currency = frappe.db.get_value("Company", company, "default_currency")
	if not currency:
		frappe.throw(_("Company {0} has no default currency.").format(frappe.bold(company)))
	return currency


def _validate_salary_component(component):
	values = frappe.db.get_value(
		"Salary Component", component, ["type", "disabled"], as_dict=True
	)
	if not values or values.disabled or values.type != "Earning":
		frappe.throw(
			_("Salary Component {0} must exist as an enabled Earning.").format(
				frappe.bold(component)
			)
		)


def _get_linked_additional_salaries(adjustment, *, docstatus=None):
	filters = {
		"ref_doctype": "Retroactive Overtime Adjustment",
		"ref_docname": adjustment,
	}
	if docstatus is not None:
		filters["docstatus"] = docstatus
	return frappe.get_all(
		"Additional Salary", filters=filters, pluck="name", order_by="creation asc"
	)


def _get_submitted_salary_slips(additional_salaries):
	if not additional_salaries:
		return []
	salary_slip = frappe.qb.DocType("Salary Slip")
	salary_detail = frappe.qb.DocType("Salary Detail")
	return (
		frappe.qb.from_(salary_slip)
		.inner_join(salary_detail)
		.on(
			(salary_detail.parent == salary_slip.name)
			& (salary_detail.parenttype == "Salary Slip")
		)
		.select(salary_slip.name)
		.where(salary_slip.docstatus == 1)
		.where(salary_detail.additional_salary.isin(additional_salaries))
		.distinct()
	).run(pluck=True)
