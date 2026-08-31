# Copyright (c) 2026, PowerPro contributors
# For license information, please see license.txt

"""Audited compensatory-rest settlement backed by one allocation per period."""

import json

import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime

from powerpro.payroll_rules.overtime_compensatory import (
	calculate_compensatory_credit,
	calculate_compensatory_reversal,
)


def protect_managed_leave_allocation(allocation, method=None):
	"""Keep the consolidated allocation writable only through this service."""
	if not allocation.meta.has_field("powerpro_overtime_managed"):
		return
	if not allocation.get("powerpro_overtime_managed"):
		return
	if allocation.flags.get("powerpro_overtime_update"):
		return
	frappe.throw(
		_(
			"This Leave Allocation is managed by PowerPro overtime. Change the linked Overtime Authorization instead."
		),
		title=_("System-managed allocation"),
	)


def protect_overtime_leave_type_from_standard_request(request, method=None):
	"""Prevent HRMS holiday requests from bypassing the overtime credit ledger."""
	settings = frappe.get_single("DGII Payroll Settings")
	if not settings.overtime_compensatory_leave_type or (
		request.leave_type != settings.overtime_compensatory_leave_type
	):
		return
	has_managed_allocation = frappe.db.exists(
		"Leave Allocation",
		{
			"employee": request.employee,
			"leave_type": request.leave_type,
			"powerpro_overtime_managed": 1,
			"docstatus": 1,
		},
	)
	if not settings.enable_overtime_compensatory_settlement and not has_managed_allocation:
		return
	if method == "before_cancel":
		allocation = request.get("leave_allocation")
		if not allocation or not frappe.db.get_value(
			"Leave Allocation", allocation, "powerpro_overtime_managed"
		):
			return
	frappe.throw(
		_(
			"Leave Type {0} is reserved for verified PowerPro overtime. Use an Overtime Authorization settlement instead."
		).format(frappe.bold(request.leave_type)),
		title=_("Overtime leave type is system-managed"),
	)


def build_compensatory_preview(authorization, settings=None, bank_state=None):
	settings = settings or frappe.get_single("DGII Payroll Settings")
	_validate_configuration(settings)
	leave_period = _get_leave_period(authorization.work_date, authorization.company)
	bank_key = (
		authorization.employee,
		authorization.company,
		settings.overtime_compensatory_leave_type,
		leave_period.name,
	)
	bank = (bank_state or {}).get(bank_key)
	if bank is None:
		bank = _get_bank_totals(*bank_key)
	try:
		conversion = calculate_compensatory_credit(
			active_hours_before=bank["active_hours"],
			current_hours=authorization.verified_hours,
			effective_days_before=bank["effective_days"],
			hours_per_day=settings.overtime_hours_per_leave_day,
			leave_increment=settings.overtime_leave_increment,
		)
	except ValueError as exc:
		frappe.throw(str(exc))

	allocation = _find_managed_allocation(
		authorization.employee,
		settings.overtime_compensatory_leave_type,
		leave_period,
	)
	if bank_state is not None:
		bank_state[bank_key] = {
			"active_hours": conversion["total_active_hours"],
			"effective_days": conversion["target_days"],
		}
	return {
		"method": "Compensatory Rest",
		"authorization": authorization.name,
		"employee": authorization.employee,
		"work_date": str(getdate(authorization.work_date)),
		"leave_period": leave_period.name,
		"leave_period_from_date": str(getdate(leave_period.from_date)),
		"leave_period_to_date": str(getdate(leave_period.to_date)),
		"leave_type": settings.overtime_compensatory_leave_type,
		"leave_allocation": allocation.name if allocation else None,
		"will_create_allocation": bool(
			conversion["days_to_credit"] and not allocation
		),
		**conversion,
	}


def create_compensatory_credit(authorization):
	frappe.db.get_value(
		authorization.doctype, authorization.name, "name", for_update=True
	)
	# Different authorizations for the same employee share one hour bank and one
	# allocation. Serializing on Employee prevents concurrent lost increments.
	frappe.db.get_value("Employee", authorization.employee, "name", for_update=True)
	if frappe.db.exists(
		"Overtime Compensatory Credit",
		{"overtime_authorization": authorization.name, "docstatus": ["<", 2]},
	):
		frappe.throw(
			_("A compensatory credit already exists for this overtime authorization."),
			title=_("Duplicate settlement blocked"),
		)
	# Recalculate after the shared Employee lock. The confirmation preview is
	# read-only and may have been produced before another request completed.
	preview = build_compensatory_preview(authorization)
	allocation = None
	if flt(preview["days_to_credit"]) > 0:
		allocation = _apply_allocation_credit(authorization, preview)
	elif preview.get("leave_allocation"):
		allocation = frappe.get_doc("Leave Allocation", preview["leave_allocation"])

	credit = frappe.new_doc("Overtime Compensatory Credit")
	credit.update({
		"overtime_authorization": authorization.name,
		"employee": authorization.employee,
		"employee_name": authorization.employee_name,
		"company": authorization.company,
		"work_date": authorization.work_date,
		"leave_period": preview["leave_period"],
		"leave_type": preview["leave_type"],
		"leave_allocation": allocation.name if allocation else None,
		"hours_per_day": preview["hours_per_day"],
		"leave_increment": preview["leave_increment"],
		"banked_hours": preview["current_hours"],
		"prior_bank_hours": preview["prior_residual_hours"],
		"credited_days": preview["days_to_credit"],
		"residual_hours_after": preview["residual_hours"],
		"credited_by": frappe.session.user,
		"credited_on": now_datetime(),
		"settlement_snapshot": json.dumps(
			preview, ensure_ascii=False, indent=2, sort_keys=True
		),
	})
	credit.flags.generated_from_overtime_settlement = True
	credit.insert(ignore_permissions=True)
	credit.flags.ignore_permissions = True
	credit.flags.generated_from_overtime_settlement = True
	credit.submit()
	return credit, allocation, preview


def reverse_compensatory_credit(authorization):
	credit_name = authorization.get("compensatory_credit") or frappe.db.get_value(
		"Overtime Compensatory Credit",
		{"overtime_authorization": authorization.name, "docstatus": 1},
		"name",
	)
	if not credit_name:
		return None
	credit = frappe.get_doc("Overtime Compensatory Credit", credit_name)
	frappe.db.get_value(credit.doctype, credit.name, "name", for_update=True)
	frappe.db.get_value("Employee", credit.employee, "name", for_update=True)
	bank = _get_bank_totals(
		credit.employee,
		credit.company,
		credit.leave_type,
		credit.leave_period,
	)
	try:
		reversal = calculate_compensatory_reversal(
			active_hours_before=bank["active_hours"],
			hours_to_reverse=credit.banked_hours,
			effective_days_before=bank["effective_days"],
			hours_per_day=credit.hours_per_day,
			leave_increment=credit.leave_increment,
		)
	except ValueError as exc:
		frappe.throw(str(exc))

	if flt(reversal["days_to_reverse"]) > 0:
		allocation_name = credit.leave_allocation
		if not allocation_name:
			leave_period = frappe.db.get_value(
				"Leave Period",
				credit.leave_period,
				["name", "from_date", "to_date"],
				as_dict=True,
			)
			allocation_row = _find_managed_allocation(
				credit.employee,
				credit.leave_type,
				leave_period,
			)
			allocation_name = allocation_row.name if allocation_row else None
		if not allocation_name:
			frappe.throw(_("No managed Leave Allocation is available for reversal."))
		allocation = frappe.get_doc("Leave Allocation", allocation_name)
		if not allocation.get("powerpro_overtime_managed"):
			frappe.throw(_("The linked Leave Allocation is no longer system-managed."))
		if abs(
			flt(allocation.new_leaves_allocated) - flt(bank["effective_days"])
		) > 0.0001:
			frappe.throw(
				_("The managed Leave Allocation no longer matches its overtime credit ledger."),
				title=_("Allocation integrity check failed"),
			)
		new_total = flt(allocation.new_leaves_allocated) - flt(
			reversal["days_to_reverse"]
		)
		if new_total < -0.0001:
			frappe.throw(_("The consolidated Leave Allocation is below the required reversal."))
		allocation.new_leaves_allocated = max(new_total, 0)
		allocation.flags.ignore_permissions = True
		allocation.flags.powerpro_overtime_update = True
		# HRMS on_update_after_submit creates the negative ledger entry and blocks
		# the reversal if approved leave has already consumed this balance.
		allocation.save()

	values = {
		"reversed_hours": credit.banked_hours,
		"reversed_days": reversal["days_to_reverse"],
		"reversed_by": frappe.session.user,
		"reversed_on": now_datetime(),
		"reversal_reason": _("Linked Overtime Authorization was cancelled."),
	}
	frappe.db.set_value(credit.doctype, credit.name, values, update_modified=False)
	for fieldname, value in values.items():
		setattr(credit, fieldname, value)
	credit.flags.ignore_permissions = True
	credit.flags.reversed_from_overtime_settlement = True
	credit.cancel()
	return {**reversal, "credit": credit.name}


def _validate_configuration(settings):
	if not settings.enable_overtime_compensatory_settlement:
		frappe.throw(
			_("Compensatory overtime settlement is disabled in DGII Payroll Settings."),
			title=_("Feature disabled"),
		)
	if not settings.overtime_compensatory_leave_type:
		frappe.throw(_("Configure the Compensatory Leave Type before settlement."))
	if not frappe.db.get_value(
		"Leave Type", settings.overtime_compensatory_leave_type, "is_compensatory"
	):
		frappe.throw(_("The configured Leave Type is not marked as compensatory."))
	meta = frappe.get_meta("Leave Allocation")
	for fieldname in (
		"powerpro_overtime_managed",
		"powerpro_overtime_leave_period",
	):
		if not meta.has_field(fieldname):
			frappe.throw(
				_("Overtime settlement metadata is not installed on Leave Allocation."),
				title=_("Migration required"),
			)


def _get_leave_period(work_date, company):
	from hrms.hr.utils import get_leave_period

	periods = get_leave_period(work_date, work_date, company) or []
	if len(periods) != 1:
		frappe.throw(
			_("Exactly one active Leave Period must cover Work Date {0}.").format(
				frappe.bold(work_date)
			)
		)
	return periods[0]


def _get_bank_totals(employee, company, leave_type, leave_period):
	rows = frappe.get_all(
		"Overtime Compensatory Credit",
		filters={
			"employee": employee,
			"company": company,
			"leave_type": leave_type,
			"leave_period": leave_period,
			"docstatus": ["in", [1, 2]],
		},
		fields=[
			"docstatus",
			"banked_hours",
			"credited_days",
			"reversed_days",
		],
	)
	active_hours = sum(
		flt(row.banked_hours) for row in rows if row.docstatus == 1
	)
	effective_days = sum(flt(row.credited_days) - flt(row.reversed_days) for row in rows)
	return {
		"active_hours": round(max(active_hours, 0), 4),
		"effective_days": round(max(effective_days, 0), 4),
	}


def _find_managed_allocation(employee, leave_type, leave_period):
	rows = frappe.get_all(
		"Leave Allocation",
		filters={
			"employee": employee,
			"leave_type": leave_type,
			"docstatus": 1,
			"to_date": [">=", leave_period.from_date],
			"from_date": ["<=", leave_period.to_date],
		},
		fields=[
			"name",
			"from_date",
			"to_date",
			"powerpro_overtime_managed",
			"powerpro_overtime_leave_period",
		],
	)
	if not rows:
		return None
	if len(rows) > 1:
		frappe.throw(_("Multiple overlapping Leave Allocations require HR review."))
	row = rows[0]
	if not row.powerpro_overtime_managed:
		frappe.throw(
			_(
				"Leave Allocation {0} overlaps this period. It will not be adopted automatically."
			).format(frappe.bold(row.name)),
			title=_("Manual allocation requires review"),
		)
	if row.powerpro_overtime_leave_period != leave_period.name:
		frappe.throw(_("The managed Leave Allocation points to a different Leave Period."))
	return row


def _apply_allocation_credit(authorization, preview):
	leave_period = frappe.db.get_value(
		"Leave Period",
		preview["leave_period"],
		["name", "from_date", "to_date"],
		as_dict=True,
	)
	allocation_row = _find_managed_allocation(
		authorization.employee,
		preview["leave_type"],
		leave_period,
	)
	if allocation_row:
		allocation = frappe.get_doc("Leave Allocation", allocation_row.name)
		frappe.db.get_value(allocation.doctype, allocation.name, "name", for_update=True)
		if abs(
			flt(allocation.new_leaves_allocated)
			- flt(preview["effective_days_before"])
		) > 0.0001:
			frappe.throw(
				_("The managed Leave Allocation no longer matches its overtime credit ledger."),
				title=_("Allocation integrity check failed"),
			)
		allocation.new_leaves_allocated = flt(allocation.new_leaves_allocated) + flt(
			preview["days_to_credit"]
		)
		allocation.flags.ignore_permissions = True
		allocation.flags.powerpro_overtime_update = True
		allocation.save()
		return allocation

	allocation = frappe.new_doc("Leave Allocation")
	allocation.update({
		"employee": authorization.employee,
		"company": authorization.company,
		"leave_type": preview["leave_type"],
		"from_date": leave_period.from_date,
		"to_date": leave_period.to_date,
		"new_leaves_allocated": preview["days_to_credit"],
		"carry_forward": bool(
			frappe.db.get_value("Leave Type", preview["leave_type"], "is_carry_forward")
		),
		"powerpro_overtime_managed": 1,
		"powerpro_overtime_leave_period": leave_period.name,
	})
	allocation.flags.ignore_permissions = True
	allocation.flags.powerpro_overtime_update = True
	allocation.insert()
	allocation.submit()
	return allocation
