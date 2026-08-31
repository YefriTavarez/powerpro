# Copyright (c) 2026, PowerPro contributors
# For license information, please see license.txt

"""Explicit preview-before-write settlement for reconciled overtime."""

import json

import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime

from powerpro.controllers.overtime_cash_settlement import (
	SETTLEMENT_CREATED,
	SETTLEMENT_PAID,
	_get_linked_additional_salaries,
	_get_overtime_rates,
	_validate_salary_component,
	before_cancel_adjustment,
	build_cash_settlement,
	cancel_cash_settlement,
	create_cash_settlement_for_source,
)
from powerpro.controllers.overtime_compensatory_settlement import (
	build_compensatory_preview,
	create_compensatory_credit,
	reverse_compensatory_credit,
)


ELIGIBLE_RECONCILIATION_STATUSES = {"Completed", "Partial", "Overrun"}
FINAL_SETTLEMENT_STATUSES = {"Created", "Paid", "Credited"}


@frappe.whitelist()
def preview_overtime_settlement(authorization, payroll_date=None):
	doc = frappe.get_doc("Overtime Authorization", authorization)
	_validate_access(doc)
	return _build_preview(doc, payroll_date=payroll_date)


@frappe.whitelist()
def settle_overtime_authorization(authorization, payroll_date=None):
	doc = frappe.get_doc("Overtime Authorization", authorization)
	_validate_access(doc)
	return _settle_authorization(doc, payroll_date=payroll_date)


@frappe.whitelist()
def preview_overtime_work_call_settlement(work_call, payroll_date=None):
	doc = frappe.get_doc("Overtime Work Call", work_call)
	if not frappe.has_permission(doc.doctype, "read", doc=doc):
		frappe.throw(_("Not permitted to read this overtime work call."), frappe.PermissionError)
	settings = _validate_settlement_role()
	rows = []
	bank_state = {}
	for authorization in _get_work_call_authorizations(doc):
		_validate_ready(authorization)
		rows.append(
			_build_preview(
				authorization,
				payroll_date=payroll_date,
				settings=settings,
				compensatory_bank_state=bank_state,
			)
		)
	return _summarize_work_call_preview(doc, rows)


@frappe.whitelist()
def settle_overtime_work_call(work_call, payroll_date=None):
	doc = frappe.get_doc("Overtime Work Call", work_call)
	if not frappe.has_permission(doc.doctype, "read", doc=doc):
		frappe.throw(_("Not permitted to read this overtime work call."), frappe.PermissionError)
	settings = _validate_settlement_role()
	authorizations = _get_work_call_authorizations(doc)
	# Validate and calculate every row before the first write. Frappe's request
	# transaction then keeps the batch atomic if any creation unexpectedly fails.
	bank_state = {}
	previews = [
		_build_preview(
			authorization,
			payroll_date=payroll_date,
			settings=settings,
			compensatory_bank_state=bank_state,
		)
		for authorization in authorizations
	]
	results = [
		_settle_authorization(
			authorization,
			payroll_date=payroll_date,
			settings=settings,
			preview=preview if authorization.planned_settlement == "Cash" else None,
		)
		for authorization, preview in zip(authorizations, previews, strict=True)
	]
	return {"work_call": doc.name, "settled": len(results), "rows": results}


def before_cancel_authorization_settlement(authorization):
	if authorization.get("settlement_method") == "Cash" or authorization.get(
		"settlement_status"
	) in {SETTLEMENT_CREATED, SETTLEMENT_PAID}:
		before_cancel_adjustment(authorization)


def cancel_authorization_settlement(authorization):
	method = authorization.get("settlement_method")
	if method == "Cash" or authorization.get("settlement_status") in {
		SETTLEMENT_CREATED,
		SETTLEMENT_PAID,
	}:
		cancel_cash_settlement(authorization)
		return
	if method == "Compensatory Rest" or authorization.get(
		"settlement_status"
	) == "Credited":
		reversal = reverse_compensatory_credit(authorization)
		frappe.db.set_value(
			authorization.doctype,
			authorization.name,
			{
				"status": "Cancelled",
				"settlement_status": "Cancelled",
			},
		)
		return reversal


def _settle_authorization(doc, *, payroll_date=None, settings=None, preview=None):
	settings = settings or _validate_settlement_role()
	frappe.db.get_value(doc.doctype, doc.name, "name", for_update=True)
	doc.reload()
	_validate_ready(doc)
	preview = preview or _build_preview(
		doc,
		payroll_date=payroll_date,
		settings=settings,
	)
	if doc.planned_settlement == "Cash":
		doc.settlement_payroll_date = getdate(payroll_date)
		settlement, values = create_cash_settlement_for_source(
			doc, _reconciliation_snapshot(doc)
		)
		frappe.db.set_value(doc.doctype, doc.name, values)
		doc.add_comment(
			"Info",
			_("Cash settlement created through Additional Salary: {0}").format(
				", ".join(settlement["additional_salaries"])
			),
		)
		return {
			"authorization": doc.name,
			"settlement_status": "Created",
			"settlement_method": "Cash",
			**settlement,
		}

	credit, allocation, preview = create_compensatory_credit(doc)
	values = {
		"settlement_status": "Credited",
		"settlement_method": "Compensatory Rest",
		"compensatory_credit": credit.name,
		"leave_allocation": allocation.name if allocation else None,
		"compensatory_hours": preview["current_hours"],
		"compensatory_days": preview["days_to_credit"],
		"compensatory_residual_hours": preview["residual_hours"],
		"settlement_created_by": frappe.session.user,
		"settlement_created_on": now_datetime(),
		"settlement_breakdown": json.dumps(
			{
				**preview,
				"compensatory_credit": credit.name,
				"leave_allocation": allocation.name if allocation else None,
			},
			ensure_ascii=False,
			indent=2,
			sort_keys=True,
		),
		"settlement_references": json.dumps(
			[name for name in (credit.name, allocation.name if allocation else None) if name],
			ensure_ascii=False,
			indent=2,
		),
	}
	frappe.db.set_value(doc.doctype, doc.name, values)
	doc.add_comment(
		"Info",
		_(
			"Compensatory overtime credited: {0} hours banked, {1} leave days added, {2} residual hours."
		).format(
			preview["current_hours"],
			preview["days_to_credit"],
			preview["residual_hours"],
		),
	)
	return {
		"authorization": doc.name,
		"settlement_status": "Credited",
		"settlement_method": "Compensatory Rest",
		"compensatory_credit": credit.name,
		"leave_allocation": allocation.name if allocation else None,
		**preview,
	}


def _build_preview(
	doc,
	*,
	payroll_date=None,
	settings=None,
	compensatory_bank_state=None,
):
	settings = settings or _validate_settlement_role()
	_validate_ready(doc)
	if doc.planned_settlement == "Cash":
		existing = _get_linked_additional_salaries(doc, docstatus=["<", 2])
		if existing:
			frappe.throw(
				_("Additional Salary already exists for this authorization: {0}").format(
					frappe.bold(", ".join(existing))
				),
				title=_("Duplicate settlement blocked"),
			)
		if not payroll_date:
			frappe.throw(_("Payroll Date is required for a Cash settlement preview."))
		doc.settlement_payroll_date = getdate(payroll_date)
		settlement = build_cash_settlement(doc, _reconciliation_snapshot(doc))
		if flt(settlement.get("unsettled_weekly_rest_hours")):
			frappe.throw(
				_("Weekly-rest hours require Compensatory Rest or manual HR review."),
				title=_("Cash settlement blocked"),
			)
		if not settlement.get("lines") or flt(settlement.get("total_amount")) <= 0:
			frappe.throw(_("The reconciliation snapshot produces no cash earning."))
		for line in settlement["lines"]:
			_validate_salary_component(line["component"])
		return {
			"method": "Cash",
			"authorization": doc.name,
			"employee": doc.employee,
			"employee_name": doc.employee_name,
			"work_date": str(getdate(doc.work_date)),
			"verified_hours": flt(doc.verified_hours),
			**settlement,
		}
	if frappe.db.exists(
		"Overtime Compensatory Credit",
		{"overtime_authorization": doc.name, "docstatus": ["<", 2]},
	):
		frappe.throw(
			_("A compensatory credit already exists for this authorization."),
			title=_("Duplicate settlement blocked"),
		)
	return build_compensatory_preview(
		doc,
		settings=settings,
		bank_state=compensatory_bank_state,
	)


def _validate_access(doc):
	if not frappe.has_permission(doc.doctype, "read", doc=doc):
		frappe.throw(_("Not permitted to read this overtime authorization."), frappe.PermissionError)
	return _validate_settlement_role()


def _validate_settlement_role():
	settings = frappe.get_single("DGII Payroll Settings")
	if not settings.enable_overtime_settlement:
		frappe.throw(
			_("Overtime settlement is disabled in DGII Payroll Settings."),
			title=_("Feature disabled"),
		)
	allowed_roles = {
		line.strip()
		for line in (settings.overtime_settlement_roles or "").splitlines()
		if line.strip()
	}
	if not allowed_roles.intersection(frappe.get_roles(frappe.session.user)):
		frappe.throw(
			_("Your roles do not permit overtime settlement."),
			frappe.PermissionError,
		)
	return settings


def _validate_ready(doc):
	if doc.docstatus != 1 or doc.status != "Approved":
		frappe.throw(_("Only a submitted approved Overtime Authorization can be settled."))
	if doc.get("settlement_status") in FINAL_SETTLEMENT_STATUSES:
		frappe.throw(
			_("This overtime authorization is already settled."),
			title=_("Duplicate settlement blocked"),
		)
	if doc.get("settlement_status") == "Cancelled":
		frappe.throw(_("A cancelled settlement cannot be recreated on this document."))
	if doc.reconciliation_status not in ELIGIBLE_RECONCILIATION_STATUSES:
		frappe.throw(
			_("Reconciliation Status {0} is not eligible for settlement.").format(
				frappe.bold(doc.reconciliation_status)
			)
		)
	if not doc.reconciled_on or flt(doc.verified_hours) <= 0:
		frappe.throw(_("Save a reconciliation snapshot with verified hours first."))
	if doc.planned_settlement not in {"Cash", "Compensatory Rest"}:
		frappe.throw(_("Choose Cash or Compensatory Rest as Planned Settlement."))
	if doc.planned_settlement == "Cash":
		classified = sum(
			flt(doc.get(fieldname))
			for fieldname in (
				"regular_35_hours",
				"regular_100_hours",
				"holiday_100_hours",
				"weekly_rest_hours",
			)
		)
		if classified <= 0:
			frappe.throw(
				_("Refresh reconciliation to freeze the payroll hour classification."),
				title=_("Settlement snapshot incomplete"),
			)


def _reconciliation_snapshot(doc):
	return {
		"regular_35_hours": flt(doc.regular_35_hours),
		"regular_100_hours": flt(doc.regular_100_hours),
		"holiday_100_hours": flt(doc.holiday_100_hours),
		"weekly_rest_hours": flt(doc.weekly_rest_hours),
		"night_hours": flt(doc.night_hours),
		"rates": _get_overtime_rates(),
	}


def _get_work_call_authorizations(work_call):
	names = frappe.get_all(
		"Overtime Authorization",
		filters={"overtime_work_call": work_call.name, "docstatus": 1},
		pluck="name",
		order_by="work_date asc, employee_name asc",
	)
	if len(names) != int(work_call.authorization_count or 0):
		frappe.throw(
			_("The overtime work call does not contain its complete authorization set."),
			title=_("Settlement blocked"),
		)
	documents = [frappe.get_doc("Overtime Authorization", name) for name in names]
	pending = [
		doc
		for doc in documents
		if doc.get("settlement_status") not in FINAL_SETTLEMENT_STATUSES
	]
	if not pending:
		frappe.throw(
			_("Every authorization in this overtime work call is already settled."),
			title=_("Nothing to settle"),
		)
	return pending


def _summarize_work_call_preview(work_call, rows):
	method = work_call.planned_settlement
	result = {
		"work_call": work_call.name,
		"method": method,
		"authorization_count": len(rows),
		"verified_hours": round(
			sum(flt(row.get("current_hours") or row.get("verified_hours")) for row in rows),
			4,
		),
		"rows": rows,
	}
	if method == "Cash":
		result["total_amount"] = round(sum(flt(row.get("total_amount")) for row in rows), 2)
		result["currency"] = next((row.get("currency") for row in rows if row.get("currency")), None)
	else:
		result["leave_days_to_credit"] = round(
			sum(flt(row.get("days_to_credit")) for row in rows), 4
		)
	return result
