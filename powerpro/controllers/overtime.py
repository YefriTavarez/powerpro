# Copyright (c) 2026, PowerPro contributors
# For license information, please see license.txt

"""Read-only reconciliation for approved overtime records."""

from datetime import datetime, time, timedelta

import frappe
from frappe import _
from frappe.utils import cint, flt, get_datetime, getdate

from powerpro.payroll_rules.overtime import (
	REGULAR_DAY,
	classify_workday,
	coerce_time,
	get_regular_35_percent_cap,
	get_shift_window,
	holiday_list_covers,
	reconcile_authorized_overtime,
)


WEEKDAY_FIELDS = {
	0: "custom_trabaja_lunes",
	1: "custom_trabaja_martes",
	2: "custom_trabaja_miercoles",
	3: "custom_trabaja_jueves",
	4: "custom_trabaja_viernes",
	5: "custom_trabaja_sabado",
	6: "custom_trabaja_domingo",
}


@frappe.whitelist()
def get_reconciliation_preview(authorization):
	"""Compare approval, schedule, holidays, and punches without saving data."""
	doc = frappe.get_doc("Overtime Authorization", authorization)
	if not frappe.has_permission("Overtime Authorization", "read", doc=doc):
		frappe.throw(
			_("Not permitted to read Overtime Authorization {0}.").format(doc.name),
			frappe.PermissionError,
		)
	if doc.docstatus != 1:
		frappe.throw(_("Only an approved Overtime Authorization can be reconciled."))

	result = _reconcile(doc, include_weekly_context=True)
	result.update({
		"authorization": doc.name,
		"read_only": True,
		"saved_documents": 0,
		"payroll_connected": False,
	})
	return result


@frappe.whitelist()
def get_retroactive_adjustment_preview(adjustment):
	"""Preview a historical adjustment or return its immutable submitted snapshot."""
	doc = frappe.get_doc("Retroactive Overtime Adjustment", adjustment)
	if not frappe.has_permission("Retroactive Overtime Adjustment", "read", doc=doc):
		frappe.throw(
			_("Not permitted to read Retroactive Overtime Adjustment {0}.").format(
				doc.name
			),
			frappe.PermissionError,
		)
	if doc.docstatus == 2:
		frappe.throw(_("A cancelled Retroactive Overtime Adjustment cannot be reconciled."))

	if doc.docstatus == 1:
		return _submitted_adjustment_snapshot(doc)

	result = reconcile_overtime_document(doc, include_weekly_context=True)
	if doc.planned_settlement == "Cash":
		from powerpro.controllers.overtime_cash_settlement import build_cash_settlement

		result["cash_settlement"] = build_cash_settlement(doc, result)
		weekly_rest_hours = flt(
			result["cash_settlement"].get("unsettled_weekly_rest_hours")
		)
		if weekly_rest_hours:
			result["warnings"].append(
				f"{weekly_rest_hours} ordinary weekly-rest hours require compensatory or manual review and are excluded from automatic cash settlement."
			)
	result.update({
		"adjustment": doc.name,
		"read_only": True,
		"saved_documents": 0,
		"payroll_connected": False,
		"snapshot": False,
	})
	return result


def reconcile_overtime_document(doc, *, include_weekly_context=True):
	"""Public app helper used by guarded controllers without saving documents."""
	return _reconcile(doc, include_weekly_context=include_weekly_context)


def _reconcile(doc, *, include_weekly_context):
	context = _get_context(doc)
	regular_before = (
		_get_verified_regular_overtime_before(doc) if include_weekly_context else 0
	)
	settings = frappe.get_single("DGII Payroll Settings")
	expected_hours = flt(settings.weekly_expected_hours)
	weekly_total_threshold = flt(settings.max_weekly_extra_hours)
	try:
		regular_cap = get_regular_35_percent_cap(
			expected_hours,
			weekly_total_threshold,
		)
	except ValueError:
		frappe.throw(
			_(
				"Max Weekly Extra Hours must be greater than Weekly Expected Hours before overtime can be reconciled."
			)
		)

	result = reconcile_authorized_overtime(
		authorization_start=doc.authorization_start,
		authorization_end=doc.authorization_end,
		maximum_hours=doc.maximum_hours,
		checkins=context["checkins"],
		day_classification=context["classification"],
		shift_start=context["shift_start"],
		shift_end=context["shift_end"],
		approved_regular_overtime_before=regular_before,
		regular_35_percent_cap=regular_cap,
		night_start=coerce_time(settings.start_night_hours, time(21, 0)),
		night_end=coerce_time(settings.end_night_hours, time(7, 0)),
	)
	result["warnings"] = [*context["warnings"], *result["warnings"]]
	result.update({
		"work_date": str(getdate(doc.work_date)),
		"shift_type": doc.shift_type,
		"holiday_list": context["holiday_list"],
		"holiday_descriptions": context["holiday_descriptions"],
		"scheduled_shift_start": _iso(context["shift_start"]),
		"scheduled_shift_end": _iso(context["shift_end"]),
		"weekly_regular_overtime_before": round(regular_before, 4),
		"regular_35_percent_weekly_cap": round(regular_cap, 4),
		"rates": {
			"regular_overtime_percent": round(flt(settings.extra_hours_rate), 4),
			"extraordinary_overtime_percent": round(
				flt(settings.extraordinary_hours_rate), 4
			),
			"night_hours_percent": round(flt(settings.night_hours_rate), 4),
		},
		"source_checkins": [_serialize_checkin(row) for row in context["checkins"]],
	})
	return result


def _get_context(doc):
	context = get_schedule_context(doc.work_date, doc.shift_type, doc.holiday_list)
	if doc.day_classification and doc.day_classification != context["classification"]:
		context["warnings"].append(
			"Approved day classification was "
			f"{doc.day_classification}; current schedule resolves "
			f"{context['classification']}."
		)
	work_date = getdate(doc.work_date)
	checkins = _get_checkins(doc.employee, work_date)
	if not checkins:
		context["warnings"].append(
			"No Employee Checkin evidence was found for this work date."
		)
	context["checkins"] = checkins
	return context


def get_schedule_context(work_date, shift_type, holiday_list=None):
	"""Resolve the schedule classification without changing any document."""
	work_date = getdate(work_date)
	shift = _get_record_values(
		"Shift Type",
		shift_type,
		[
			"start_time",
			"end_time",
			"holiday_list",
			"custom_hora_salida_viernes",
			*WEEKDAY_FIELDS.values(),
		],
	)
	if not shift:
		frappe.throw(_("Shift Type {0} does not exist.").format(frappe.bold(shift_type)))

	holiday_list = holiday_list or shift.get("holiday_list")
	holiday_list_coverage = _get_holiday_list_coverage(holiday_list, work_date)
	holidays = _get_holidays(holiday_list, work_date)
	has_legal_holiday = any(not row.get("weekly_off") for row in holidays)
	has_weekly_off = any(row.get("weekly_off") for row in holidays)

	workday_field = WEEKDAY_FIELDS[work_date.weekday()]
	if workday_field in shift:
		is_shift_workday = bool(cint(shift.get(workday_field)))
	else:
		is_shift_workday = not has_weekly_off

	classification = classify_workday(
		is_shift_workday=is_shift_workday,
		has_legal_holiday=has_legal_holiday,
	)
	shift_start, shift_end = get_shift_window(
		work_date,
		shift.get("start_time"),
		shift.get("end_time"),
		shift.get("custom_hora_salida_viernes"),
	)
	warnings = []
	if not holiday_list:
		warnings.append("No Holiday List could be resolved for this authorization.")
	elif not holiday_list_coverage["covers_work_date"]:
		warnings.append(
			f"Holiday List {holiday_list} does not cover work date {work_date}."
		)

	return {
		"classification": classification,
		"shift_start": shift_start,
		"shift_end": shift_end,
		"holiday_list": holiday_list,
		"holiday_list_from_date": holiday_list_coverage["from_date"],
		"holiday_list_to_date": holiday_list_coverage["to_date"],
		"holiday_list_covers_work_date": holiday_list_coverage["covers_work_date"],
		"holiday_descriptions": [row.get("description") for row in holidays if row.get("description")],
		"warnings": warnings,
	}


def _get_holiday_list_coverage(holiday_list, work_date):
	if not holiday_list:
		return {"from_date": None, "to_date": None, "covers_work_date": False}
	values = frappe.db.get_value(
		"Holiday List", holiday_list, ["from_date", "to_date"], as_dict=True
	)
	if not values:
		return {"from_date": None, "to_date": None, "covers_work_date": False}
	from_date = getdate(values.from_date) if values.from_date else None
	to_date = getdate(values.to_date) if values.to_date else None
	covers_work_date = holiday_list_covers(work_date, from_date, to_date)
	return {
		"from_date": str(from_date) if from_date else None,
		"to_date": str(to_date) if to_date else None,
		"covers_work_date": covers_work_date,
	}


def _get_verified_regular_overtime_before(doc):
	work_date = getdate(doc.work_date)
	week_start = work_date - timedelta(days=work_date.weekday())
	week_end = week_start + timedelta(days=6)
	total = 0.0
	for doctype in ("Overtime Authorization", "Retroactive Overtime Adjustment"):
		if not frappe.db.exists("DocType", doctype):
			continue
		names = frappe.get_all(
			doctype,
			filters={
				"employee": doc.employee,
				"docstatus": 1,
				"work_date": ["between", [week_start, week_end]],
				"authorization_start": ["<", doc.authorization_start],
			},
			pluck="name",
			order_by="authorization_start asc",
		)
		for name in names:
			if doctype == doc.doctype and name == doc.name:
				continue
			previous = frappe.get_doc(doctype, name)
			if doctype == "Retroactive Overtime Adjustment":
				if previous.day_classification == REGULAR_DAY:
					total += flt(previous.verified_hours)
				continue
			context = _get_context(previous)
			if context["classification"] != REGULAR_DAY:
				continue
			result = _reconcile(previous, include_weekly_context=False)
			total += flt(result["verified_hours"])
	return total


def _get_record_values(doctype, name, requested_fields):
	if not name:
		return None
	meta = frappe.get_meta(doctype)
	fields = [fieldname for fieldname in requested_fields if meta.has_field(fieldname)]
	if not fields:
		return frappe._dict()
	return frappe.db.get_value(doctype, name, fields, as_dict=True)


def _get_holidays(holiday_list, work_date):
	if not holiday_list:
		return []
	meta = frappe.get_meta("Holiday")
	fields = ["description"]
	if meta.has_field("weekly_off"):
		fields.append("weekly_off")
	rows = frappe.get_all(
		"Holiday",
		filters={"parent": holiday_list, "holiday_date": work_date},
		fields=fields,
		order_by="idx asc",
	)
	for row in rows:
		row["weekly_off"] = bool(cint(row.get("weekly_off")))
	return rows


def _get_checkins(employee, work_date):
	meta = frappe.get_meta("Employee Checkin")
	fields = [
		fieldname
		for fieldname in ("name", "time", "log_type", "accion", "shift")
		if fieldname == "name" or meta.has_field(fieldname)
	]
	window_start = datetime.combine(work_date, time.min)
	window_end = datetime.combine(work_date, time.min) + timedelta(days=2)
	return frappe.get_all(
		"Employee Checkin",
		filters={
			"employee": employee,
			"time": ["between", [window_start, window_end]],
		},
		fields=fields,
		order_by="time asc",
	)


def _iso(value):
	return get_datetime(value).isoformat() if value else None


def _serialize_checkin(row):
	return {
		key: _iso(value) if key == "time" else value
		for key, value in row.items()
		if key in {"name", "time", "log_type", "accion", "shift"}
	}


def _submitted_adjustment_snapshot(doc):
	settlement = frappe.parse_json(doc.get("settlement_breakdown") or "{}")
	references = frappe.parse_json(doc.get("settlement_references") or "[]")
	return {
		"adjustment": doc.name,
		"classification": doc.day_classification,
		"verified_hours": flt(doc.verified_hours),
		"regular_35_hours": flt(doc.regular_35_hours),
		"regular_100_hours": flt(doc.regular_100_hours),
		"holiday_100_hours": flt(doc.holiday_100_hours),
		"weekly_rest_hours": flt(doc.weekly_rest_hours),
		"night_hours": flt(doc.night_hours),
		"warnings": (doc.reconciliation_warnings or "").splitlines(),
		"intervals": frappe.parse_json(doc.reconciliation_intervals or "[]"),
		"source_checkins": frappe.parse_json(doc.source_checkins or "[]"),
		"read_only": True,
		"rates": _get_current_overtime_rates(),
		"cash_settlement": settlement or None,
		"settlement_status": doc.get("settlement_status"),
		"saved_documents": len(references),
		"payroll_connected": bool(references),
		"snapshot": True,
		"reconciled_by": doc.reconciled_by,
		"reconciled_on": _iso(doc.reconciled_on),
	}


def _get_current_overtime_rates():
	settings = frappe.get_single("DGII Payroll Settings")
	return {
		"regular_overtime_percent": round(flt(settings.extra_hours_rate), 4),
		"extraordinary_overtime_percent": round(
			flt(settings.extraordinary_hours_rate), 4
		),
		"night_hours_percent": round(flt(settings.night_hours_rate), 4),
	}
