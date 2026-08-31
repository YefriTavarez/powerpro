"""Pure helpers for company-requested overtime work calls."""

from __future__ import annotations

from datetime import datetime, time, timedelta


CHECKIN_WARNING_PREFIXES = (
	"Duplicate start",
	"Orphan stop",
	"Invalid punch",
	"Open work",
	"Unrecognized",
)


def build_authorization_window(work_date, start_time, end_time):
	"""Build a same-day or overnight authorization window."""
	work_date = _as_date(work_date)
	start_clock = _coerce_time(start_time)
	end_clock = _coerce_time(end_time)
	if start_clock is None or end_clock is None:
		raise ValueError("Start Time and End Time are required")
	start = datetime.combine(work_date, start_clock)
	end = datetime.combine(work_date, end_clock)
	if end <= start:
		end += timedelta(days=1)
	return start, end


def requested_hours(work_date, start_time, end_time):
	start, end = build_authorization_window(work_date, start_time, end_time)
	return round((end - start).total_seconds() / 3600, 4)


def derive_reconciliation_snapshot(
	*,
	authorization_start,
	authorization_end,
	maximum_hours,
	reconciliation,
	evaluation_time,
):
	"""Turn a read-only reconciliation result into operational adherence fields."""
	start = _as_datetime(authorization_start)
	end = _as_datetime(authorization_end)
	evaluation_time = _as_datetime(evaluation_time)
	requested = max(float(maximum_hours or 0), 0)
	verified = max(float(reconciliation.get("verified_hours") or 0), 0)
	unapproved = max(float(reconciliation.get("unapproved_hours") or 0), 0)
	intervals = reconciliation.get("intervals") or []
	warnings = [str(value) for value in (reconciliation.get("warnings") or []) if value]
	source_checkins = reconciliation.get("source_checkins") or []

	actual_start = min(
		(_as_datetime(row["start"]) for row in intervals if row.get("start")),
		default=None,
	)
	actual_end = max(
		(_as_datetime(row["end"]) for row in intervals if row.get("end")),
		default=None,
	)
	missing = max(requested - verified, 0)
	adherence = min((verified / requested * 100) if requested else 0, 100)
	late_minutes = max(
		((actual_start - start).total_seconds() / 60) if actual_start else 0,
		0,
	)
	early_departure_minutes = max(
		((end - actual_end).total_seconds() / 60) if actual_end else 0,
		0,
	)

	if evaluation_time < end:
		status = "Scheduled"
	elif any(warning.startswith(CHECKIN_WARNING_PREFIXES) for warning in warnings):
		status = "Check-in Issue"
	elif not source_checkins:
		status = "Absent"
	elif unapproved > 0.0001:
		status = "Overrun"
	elif verified <= 0.0001:
		status = "Absent"
	elif missing > 0.0001:
		status = "Partial"
	else:
		status = "Completed"

	return {
		"actual_start": actual_start,
		"actual_end": actual_end,
		"verified_hours": round(verified, 4),
		"regular_35_hours": round(
			max(float(reconciliation.get("regular_35_hours") or 0), 0), 4
		),
		"regular_100_hours": round(
			max(float(reconciliation.get("regular_100_hours") or 0), 0), 4
		),
		"holiday_100_hours": round(
			max(float(reconciliation.get("holiday_100_hours") or 0), 0), 4
		),
		"weekly_rest_hours": round(
			max(float(reconciliation.get("weekly_rest_hours") or 0), 0), 4
		),
		"night_hours": round(
			max(float(reconciliation.get("night_hours") or 0), 0), 4
		),
		"missing_hours": round(missing, 4),
		"unapproved_hours": round(unapproved, 4),
		"adherence_percent": round(adherence, 2),
		"late_minutes": round(late_minutes, 2),
		"early_departure_minutes": round(early_departure_minutes, 2),
		"reconciliation_status": status,
	}


def _as_datetime(value):
	if isinstance(value, datetime):
		return value
	return datetime.fromisoformat(str(value))


def _as_date(value):
	if isinstance(value, datetime):
		return value.date()
	if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
		return value
	return datetime.fromisoformat(str(value)).date()


def _coerce_time(value):
	if value is None or value == "":
		return None
	if isinstance(value, time):
		return value
	if isinstance(value, datetime):
		return value.time()
	if isinstance(value, timedelta):
		seconds = int(value.total_seconds()) % (24 * 60 * 60)
		return time(seconds // 3600, (seconds % 3600) // 60, seconds % 60)
	text = str(value).split(".", 1)[0]
	for template in ("%H:%M:%S", "%H:%M"):
		try:
			return datetime.strptime(text, template).time()
		except ValueError:
			continue
	raise ValueError(f"Invalid time value: {value}")
