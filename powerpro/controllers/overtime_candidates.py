# Copyright (c) 2026, PowerPro contributors
# For license information, please see license.txt

"""Generate review-only overtime candidates from existing check-in evidence."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, time, timedelta

import frappe
from frappe import _
from frappe.utils import cint, get_datetime, getdate, now_datetime

from powerpro.controllers.overtime import get_schedule_context
from powerpro.payroll_rules.overtime_candidates import (
	ELIGIBILITY_PENDING,
	NEEDS_CHECKIN_REVIEW,
	OPEN,
	analyze_overtime_candidate,
	candidate_dedupe_key,
	parse_designation_keywords,
)


REVIEWABLE_STATUSES = {OPEN, ELIGIBILITY_PENDING, NEEDS_CHECKIN_REVIEW}
DECISIONS = {
	"Approved Cash",
	"Approved Compensatory Rest",
	"Rejected",
	"Invalid Check-in",
}
APPROVAL_ROLES = {"HR Manager", "Manufacturing Manager", "System Manager"}
DEFAULT_PLANT_KEYWORDS = "Operador\nAuxiliar\nMecánico\nElectricista\nInspector\nPrensista\nTroquelador"


def scheduled_generate_overtime_candidates():
	"""Feature-gated hourly entry point. Scheduler transactions commit normally."""
	if not _generation_enabled():
		return {"disabled": True, "created": 0, "updated": 0}
	return _generate_overtime_candidates(dry_run=False)


@frappe.whitelist()
def generate_overtime_candidates(
	from_date=None,
	to_date=None,
	dry_run=1,
):
	"""Preview or idempotently generate candidates for a bounded date range."""
	_assert_review_role()
	return _generate_overtime_candidates(
		from_date=from_date,
		to_date=to_date,
		dry_run=bool(cint(dry_run)),
	)


def _generate_overtime_candidates(from_date=None, to_date=None, dry_run=True):
	"""Internal generator used by the role-checked API and trusted scheduler."""
	dry_run = bool(cint(dry_run))
	if not dry_run and not _generation_enabled():
		frappe.throw(
			_("Overtime Candidate Generation is disabled in DGII Payroll Settings."),
			title=_("Feature disabled"),
		)

	settings = frappe.get_single("DGII Payroll Settings")
	to_date = getdate(to_date or getdate(now_datetime()) - timedelta(days=1))
	lookback_days = max(cint(settings.get("overtime_candidate_lookback_days") or 2), 1)
	from_date = getdate(from_date or to_date - timedelta(days=lookback_days - 1))
	if to_date < from_date:
		frappe.throw(_("To Date must be on or after From Date."))
	if (to_date - from_date).days > 31:
		frappe.throw(_("Overtime candidate generation is limited to 32 calendar days per run."))

	threshold = max(
		cint(settings.get("overtime_candidate_threshold_minutes") or 15), 1
	)
	keywords = parse_designation_keywords(
		settings.get("overtime_candidate_designation_keywords") or DEFAULT_PLANT_KEYWORDS
	)
	employees = _get_active_employees()
	checkins_by_employee = _get_checkins_by_employee(from_date, to_date)
	result = {
		"dry_run": dry_run,
		"from_date": str(from_date),
		"to_date": str(to_date),
		"threshold_minutes": threshold,
		"created": 0,
		"updated": 0,
		"unchanged": 0,
		"skipped_existing_overtime": 0,
		"superseded": 0,
		"candidates": [],
	}

	work_date = from_date
	while work_date <= to_date:
		for employee in employees:
			rows = checkins_by_employee.get(employee.name, [])
			if not rows:
				continue
			candidate = _build_candidate(
				employee,
				work_date,
				rows,
				threshold=threshold,
				keywords=keywords,
			)
			if not candidate:
				continue
			existing_overtime = _get_existing_overtime_record(employee.name, work_date)
			if existing_overtime:
				result["skipped_existing_overtime"] += 1
				if not dry_run and _supersede_open_candidate(
					employee.name, work_date, existing_overtime
				):
					result["superseded"] += 1
				continue

			preview = {
				key: candidate.get(key)
				for key in (
					"employee",
					"employee_name",
					"work_date",
					"shift_type",
					"day_classification",
					"status",
					"evidence_status",
					"late_minutes",
					"qualifying_hours",
					"scope_reason",
				)
			}
			result["candidates"].append(preview)
			if dry_run:
				continue
			operation = _upsert_candidate(candidate)
			result[operation] += 1
		work_date += timedelta(days=1)

	result["candidate_count"] = len(result["candidates"])
	return result


@frappe.whitelist()
def decide_overtime_candidate(candidate, decision, reason):
	"""Record a supervisor decision without creating payroll or leave documents."""
	_assert_review_role()
	decision = str(decision or "").strip()
	reason = str(reason or "").strip()
	if decision not in DECISIONS:
		frappe.throw(_("Unsupported overtime candidate decision."))
	if not reason:
		frappe.throw(_("A decision reason is required."))

	doc = frappe.get_doc("Overtime Candidate", candidate)
	if not frappe.has_permission("Overtime Candidate", "write", doc=doc):
		frappe.throw(_("Not permitted to review this Overtime Candidate."), frappe.PermissionError)
	if doc.status not in REVIEWABLE_STATUSES:
		frappe.throw(
			_("Overtime Candidate {0} already has a final decision.").format(
				frappe.bold(doc.name)
			)
		)

	if decision.startswith("Approved"):
		if doc.evidence_status != "Ready":
			frappe.throw(_("Check-in evidence must be ready before approval."))
		employee = frappe.db.get_value(
			"Employee",
			doc.employee,
			["overtime_eligible", "overtime_approver"],
			as_dict=True,
		)
		if not employee or not employee.overtime_eligible:
			frappe.throw(_("The employee must be marked overtime-eligible before approval."))
		if employee.overtime_approver != frappe.session.user:
			frappe.throw(
				_("Only the employee's assigned Overtime Approver {0} may approve.").format(
					frappe.bold(employee.overtime_approver or _("Not configured"))
				),
				frappe.PermissionError,
			)

	doc.status = decision
	doc.proposed_settlement = (
		"Cash" if decision == "Approved Cash"
		else "Compensatory Rest" if decision == "Approved Compensatory Rest"
		else None
	)
	doc.decision_reason = reason
	doc.decided_by = frappe.session.user
	doc.decided_on = now_datetime()
	doc.flags.allow_candidate_decision = True
	doc.save()
	return {
		"candidate": doc.name,
		"status": doc.status,
		"saved_documents": 1,
		"payroll_documents_created": 0,
		"leave_documents_created": 0,
	}


def _build_candidate(employee, work_date, all_rows, *, threshold, keywords):
	shift_assignment, resolved_shift = _resolve_shift(
		employee.name, work_date, employee.default_shift
	)
	possible_shifts = [resolved_shift]
	for row in all_rows:
		row_time = get_datetime(row.time)
		if getdate(row_time) == work_date:
			possible_shifts.append(row.get("shift"))
	possible_shifts = list(dict.fromkeys(shift for shift in possible_shifts if shift))
	if not possible_shifts:
		return None

	best = None
	for shift_type in possible_shifts:
		try:
			holiday_list = _resolve_holiday_list(employee, shift_type)
			context = get_schedule_context(work_date, shift_type, holiday_list)
		except frappe.ValidationError:
			continue
		if not context["shift_start"] or not context["shift_end"]:
			continue
		window_start = context["shift_start"] - timedelta(hours=4)
		window_end = (
			context["shift_start"] + timedelta(days=1)
			if getdate(context["shift_end"]) > getdate(context["shift_start"])
			else datetime.combine(work_date + timedelta(days=1), time.min)
		)
		checkins = [
			dict(row)
			for row in all_rows
			if window_start <= get_datetime(row.time) < window_end
		]
		if not checkins:
			continue
		analysis = analyze_overtime_candidate(
			checkins=checkins,
			day_classification=context["classification"],
			shift_start=context["shift_start"],
			shift_end=context["shift_end"],
			threshold_minutes=threshold,
			overtime_eligible=employee.overtime_eligible,
			designation=employee.designation,
			designation_keywords=keywords,
		)
		if context["warnings"] and analysis["has_signal"]:
			analysis["evidence_status"] = "Review Required"
			analysis["status"] = NEEDS_CHECKIN_REVIEW
		if not analysis["has_signal"] or not analysis["in_scope"]:
			continue
		rank = (
			analysis["evidence_status"] == "Ready",
			analysis["qualifying_hours"],
			analysis["late_minutes"],
		)
		if best and rank <= best[0]:
			continue
		best = (rank, shift_type, holiday_list, context, analysis)

	if not best:
		return None
	_, shift_type, holiday_list, context, analysis = best
	serialized_checkins = [_serialize_checkin(row) for row in analysis["checkins"]]
	evidence_hash = hashlib.sha256(
		json.dumps(serialized_checkins, sort_keys=True).encode()
	).hexdigest()
	return {
		"doctype": "Overtime Candidate",
		"dedupe_key": candidate_dedupe_key(employee.name, work_date),
		"employee": employee.name,
		"employee_name": employee.employee_name,
		"company": employee.company,
		"department": employee.department,
		"designation": employee.designation,
		"overtime_eligible_snapshot": employee.overtime_eligible,
		"approver": employee.overtime_approver,
		"work_date": work_date,
		"shift_assignment": shift_assignment if shift_type == resolved_shift else None,
		"shift_type": shift_type,
		"holiday_list": holiday_list,
		"day_classification": context["classification"],
		"legal_holiday_description": "; ".join(context["holiday_descriptions"]),
		"scheduled_start": context["shift_start"],
		"scheduled_end": context["shift_end"],
		"first_valid_in": analysis["first_valid_in"],
		"last_valid_out": analysis["last_valid_out"],
		"late_minutes": analysis["late_minutes"],
		"qualifying_hours": analysis["qualifying_hours"],
		"evidence_status": analysis["evidence_status"],
		"scope_reason": analysis["scope_reason"],
		"evidence_warnings": "\n".join([*context["warnings"], *analysis["warnings"]]),
		"verified_intervals": json.dumps(analysis["intervals"], indent=2),
		"source_checkins": json.dumps(serialized_checkins, indent=2),
		"evidence_hash": evidence_hash,
		"status": analysis["status"],
		"generated_on": now_datetime(),
	}


def _upsert_candidate(values):
	name = frappe.db.get_value(
		"Overtime Candidate", {"dedupe_key": values["dedupe_key"]}, "name"
	)
	if not name:
		doc = frappe.get_doc(values)
		doc.flags.generated_by_overtime_scanner = True
		doc.insert(ignore_permissions=True)
		return "created"

	doc = frappe.get_doc("Overtime Candidate", name)
	if doc.status not in REVIEWABLE_STATUSES:
		return "unchanged"
	if doc.evidence_hash == values["evidence_hash"] and doc.status == values["status"]:
		return "unchanged"
	doc.update({key: value for key, value in values.items() if key != "doctype"})
	doc.flags.generated_by_overtime_scanner = True
	doc.save(ignore_permissions=True)
	return "updated"


def _get_active_employees():
	meta = frappe.get_meta("Employee")
	fields = [
		"name",
		"employee_name",
		"company",
		"department",
		"designation",
		"default_shift",
		"holiday_list",
	]
	for fieldname in ("overtime_eligible", "overtime_approver"):
		if meta.has_field(fieldname):
			fields.append(fieldname)
	return frappe.get_all(
		"Employee", filters={"status": "Active"}, fields=fields, order_by="name asc"
	)


def _get_checkins_by_employee(from_date, to_date):
	meta = frappe.get_meta("Employee Checkin")
	fields = [
		fieldname
		for fieldname in ("name", "employee", "time", "log_type", "accion", "shift")
		if fieldname in {"name", "employee"} or meta.has_field(fieldname)
	]
	rows = frappe.get_all(
		"Employee Checkin",
		filters={
			"time": [
				"between",
				[
					datetime.combine(from_date, time.min) - timedelta(hours=4),
					datetime.combine(to_date + timedelta(days=2), time.min),
				],
			],
		},
		fields=fields,
		order_by="employee asc, time asc",
	)
	result = {}
	for row in rows:
		result.setdefault(row.employee, []).append(row)
	return result


def _resolve_shift(employee, work_date, default_shift):
	if not frappe.db.exists("DocType", "Shift Assignment"):
		return None, default_shift
	meta = frappe.get_meta("Shift Assignment")
	fields = ["name", "shift_type", "start_date"]
	if meta.has_field("end_date"):
		fields.append("end_date")
	assignments = frappe.get_all(
		"Shift Assignment",
		filters={
			"employee": employee,
			"docstatus": 1,
			"start_date": ["<=", work_date],
		},
		fields=fields,
		order_by="start_date desc, creation desc",
	)
	for assignment in assignments:
		if assignment.get("end_date") and getdate(assignment.end_date) < work_date:
			continue
		return assignment.name, assignment.shift_type
	return None, default_shift


def _resolve_holiday_list(employee, shift_type):
	return (
		frappe.db.get_value("Shift Type", shift_type, "holiday_list")
		or employee.holiday_list
		or frappe.db.get_value("Company", employee.company, "default_holiday_list")
	)


def _get_existing_overtime_record(employee, work_date):
	for doctype in ("Overtime Authorization", "Retroactive Overtime Adjustment"):
		if not frappe.db.exists("DocType", doctype):
			continue
		name = frappe.db.get_value(
			doctype,
			{"employee": employee, "work_date": work_date, "docstatus": ["<", 2]},
			"name",
		)
		if name:
			return f"{doctype}: {name}"
	return None


def _supersede_open_candidate(employee, work_date, existing_overtime):
	name = frappe.db.get_value(
		"Overtime Candidate",
		{"dedupe_key": candidate_dedupe_key(employee, work_date)},
		"name",
	)
	if not name:
		return False
	doc = frappe.get_doc("Overtime Candidate", name)
	if doc.status not in REVIEWABLE_STATUSES:
		return False
	doc.status = "Superseded"
	doc.decision_reason = _("Superseded by existing {0}").format(existing_overtime)
	doc.decided_by = frappe.session.user
	doc.decided_on = now_datetime()
	doc.flags.generated_by_overtime_scanner = True
	doc.save(ignore_permissions=True)
	return True


def _serialize_checkin(row):
	return {
		key: get_datetime(value).isoformat() if key == "time" else value
		for key, value in dict(row).items()
		if key in {"name", "time", "log_type", "accion", "shift"}
	}


def _generation_enabled():
	meta = frappe.get_meta("DGII Payroll Settings")
	return bool(
		meta.has_field("enable_overtime_candidate_generation")
		and cint(
			frappe.db.get_single_value(
				"DGII Payroll Settings", "enable_overtime_candidate_generation"
			)
		)
	)


def _assert_review_role():
	if not APPROVAL_ROLES.intersection(frappe.get_roles()):
		frappe.throw(
			_("HR Manager, Manufacturing Manager, or System Manager role is required."),
			frappe.PermissionError,
		)
