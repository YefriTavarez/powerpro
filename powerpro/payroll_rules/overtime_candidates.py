"""Pure rules for surfacing overtime candidates from attendance evidence.

Candidates are review work items, not authorization or payroll.  These rules
never create payable hours, Additional Salary, Leave Allocation, or accounting
records.
"""

from __future__ import annotations

from datetime import datetime

from powerpro.payroll_rules.overtime import (
	HOLIDAY_ON_WEEKLY_REST,
	LEGAL_HOLIDAY,
	REGULAR_DAY,
	WEEKLY_REST,
	WorkInterval,
	build_work_intervals,
)


OPEN = "Open"
ELIGIBILITY_PENDING = "Eligibility Pending"
NEEDS_CHECKIN_REVIEW = "Needs Check-in Review"
LEGAL_HOLIDAY_CLASSIFICATIONS = {LEGAL_HOLIDAY, HOLIDAY_ON_WEEKLY_REST}


def parse_designation_keywords(value):
	"""Normalize a newline/comma separated list without hard-coding plant roles."""
	if isinstance(value, (list, tuple, set)):
		items = value
	else:
		items = str(value or "").replace(",", "\n").splitlines()
	return tuple(sorted({str(item).strip().casefold() for item in items if str(item).strip()}))


def designation_matches_keywords(designation, keywords):
	designation = str(designation or "").strip().casefold()
	return bool(designation) and any(
		keyword in designation for keyword in parse_designation_keywords(keywords)
	)


def candidate_dedupe_key(employee, work_date):
	return f"{str(employee or '').strip()}::{str(work_date or '').split(' ', 1)[0]}"


def analyze_overtime_candidate(
	*,
	checkins,
	day_classification,
	shift_start,
	shift_end,
	threshold_minutes,
	overtime_eligible,
	designation=None,
	designation_keywords=None,
):
	"""Return a conservative candidate preview for one employee/work date.

	Regular workdays require a final punch at least ``threshold_minutes`` after
	the shift.  Legal holidays are always surfaced when there is work evidence.
	A weekly rest day on its own is deliberately excluded.  Ambiguous punches
	remain visible but are routed to manual check-in review.
	"""
	shift_start = _as_datetime(shift_start)
	shift_end = _as_datetime(shift_end)
	threshold_minutes = max(float(threshold_minutes or 0), 0)
	deduplicated, duplicate_count = _deduplicate_checkins(checkins)
	intervals, warnings = build_work_intervals(deduplicated)
	if duplicate_count:
		warnings.append(f"Ignored {duplicate_count} exact duplicate check-in(s)")

	first_in = min((interval.start for interval in intervals), default=None)
	last_out = _last_final_out_time(deduplicated)

	late_minutes = max(
		((last_out - shift_end).total_seconds() / 60) if last_out else 0,
		0,
	)
	qualifying = []
	if day_classification == REGULAR_DAY:
		qualifying = _intersections_after(intervals, shift_end)
		has_signal = late_minutes >= threshold_minutes and late_minutes > 0
	elif day_classification in LEGAL_HOLIDAY_CLASSIFICATIONS:
		qualifying = list(intervals)
		has_signal = bool(deduplicated)
	elif day_classification == WEEKLY_REST:
		has_signal = False
	else:
		raise ValueError(f"Unsupported day classification: {day_classification}")

	qualifying_hours = round(sum(interval.hours for interval in qualifying), 4)
	evidence_ready = bool(qualifying) and bool(last_out) and not any(
		warning.startswith(("Duplicate start", "Orphan stop", "Invalid punch", "Open work", "Unrecognized"))
		for warning in warnings
	)
	is_legal_holiday = day_classification in LEGAL_HOLIDAY_CLASSIFICATIONS
	in_scope = bool(overtime_eligible) or designation_matches_keywords(
		designation, designation_keywords
	) or is_legal_holiday

	status = None
	if has_signal and in_scope:
		if not evidence_ready:
			status = NEEDS_CHECKIN_REVIEW
		elif not overtime_eligible:
			status = ELIGIBILITY_PENDING
		else:
			status = OPEN

	return {
		"has_signal": has_signal,
		"in_scope": in_scope,
		"status": status,
		"evidence_status": "Ready" if evidence_ready else "Review Required",
		"scope_reason": _scope_reason(
			overtime_eligible=bool(overtime_eligible),
			designation_match=designation_matches_keywords(designation, designation_keywords),
			legal_holiday=is_legal_holiday,
		),
		"first_valid_in": first_in.isoformat() if first_in else None,
		"last_valid_out": last_out.isoformat() if last_out else None,
		"late_minutes": round(late_minutes, 2),
		"qualifying_hours": qualifying_hours,
		"warnings": warnings,
		"intervals": [
			{"start": interval.start.isoformat(), "end": interval.end.isoformat()}
			for interval in qualifying
		],
		"checkins": deduplicated,
	}


def _deduplicate_checkins(checkins):
	rows = []
	seen = set()
	duplicates = 0
	for row in checkins or []:
		normalized = dict(row)
		if normalized.get("time"):
			normalized["time"] = _as_datetime(normalized["time"])
		key = (
			normalized.get("time"),
			str(normalized.get("accion") or normalized.get("log_type") or "").strip().casefold(),
			str(normalized.get("shift") or "").strip(),
		)
		if key in seen:
			duplicates += 1
			continue
		seen.add(key)
		rows.append(normalized)
	return rows, duplicates


def _last_final_out_time(checkins):
	stops = []
	for row in checkins:
		action = " ".join(str(row.get("accion") or "").strip().upper().split())
		log_type = str(row.get("log_type") or "").strip().upper()
		if action in {"OUT", "FIN JORNADA", "FIN DE JORNADA", "SALIDA"} or (
			not action and log_type == "OUT"
		):
			stops.append(_as_datetime(row["time"]))
	return max(stops) if stops else None


def _intersections_after(intervals, boundary):
	result = []
	for interval in intervals:
		start = max(interval.start, boundary)
		if interval.end > start:
			result.append(WorkInterval(start, interval.end))
	return result


def _scope_reason(*, overtime_eligible, designation_match, legal_holiday):
	reasons = []
	if overtime_eligible:
		reasons.append("Employee marked overtime-eligible")
	if designation_match:
		reasons.append("Plant designation matched configured keywords")
	if legal_holiday:
		reasons.append("Legal holiday work evidence")
	return "; ".join(reasons)


def _as_datetime(value):
	if isinstance(value, datetime):
		return value
	return datetime.fromisoformat(str(value))
