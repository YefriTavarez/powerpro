"""Pure guardrails for the temporary retroactive-overtime exception path."""

from datetime import date, datetime, timedelta


def is_submission_deadline_open(deadline, reference_date):
	return bool(deadline) and _as_date(reference_date) <= _as_date(deadline)


def is_adjustment_date_allowed(work_date, from_date, to_date):
	if not work_date or not from_date or not to_date:
		return False
	return _as_date(from_date) <= _as_date(work_date) <= _as_date(to_date)


def is_completed_historical_window(authorization_end, reference_datetime):
	return bool(authorization_end) and _as_datetime(authorization_end) <= _as_datetime(
		reference_datetime
	)


def is_review_window_on_work_date(
	work_date,
	authorization_start,
	authorization_end,
	*,
	allow_overnight=False,
):
	"""Keep one adjustment tied to one work date.

	A shift that genuinely crosses midnight may end on the following calendar
	date. Day shifts must start and end on ``work_date``.
	"""
	if not work_date or not authorization_start or not authorization_end:
		return False

	work_date = _as_date(work_date)
	start = _as_datetime(authorization_start)
	end = _as_datetime(authorization_end)
	latest_end_date = work_date + timedelta(days=1 if allow_overnight else 0)
	return start.date() == work_date and end.date() <= latest_end_date


def select_last_valid_out_checkin(
	checkins,
	shift_start,
	shift_end,
	*,
	shift_type=None,
):
	"""Return the last final OUT that can belong to one shift occurrence.

	Day shifts are bounded by the end of ``work_date``. Overnight shifts may
	use an OUT on the following date, but never one at or after the next shift
	start. A populated check-in shift must match the resolved employee shift.
	"""
	shift_start = _as_datetime(shift_start)
	shift_end = _as_datetime(shift_end)
	if shift_end <= shift_start:
		return None

	is_overnight = shift_end.date() > shift_start.date()
	window_end = (
		shift_start + timedelta(days=1)
		if is_overnight
		else datetime.combine(shift_start.date() + timedelta(days=1), datetime.min.time())
	)
	candidates = []
	for row in checkins or []:
		checkin_time = _row_value(row, "time")
		if not checkin_time:
			continue
		checkin_time = _as_datetime(checkin_time)
		if checkin_time < shift_end or checkin_time >= window_end:
			continue

		checkin_shift = _row_value(row, "shift")
		if shift_type and checkin_shift and checkin_shift != shift_type:
			continue
		if not _is_out_checkin(row):
			continue
		candidates.append((checkin_time, row))

	return max(candidates, key=lambda candidate: candidate[0])[1] if candidates else None


def _is_out_checkin(row):
	action = " ".join(
		str(_row_value(row, "accion") or "").strip().casefold().split()
	)
	if action:
		return action in {"fin jornada", "fin de jornada", "salida", "out"}

	log_type = str(_row_value(row, "log_type") or "").strip().upper()
	return log_type == "OUT"


def _row_value(row, key):
	if hasattr(row, "get"):
		return row.get(key)
	return getattr(row, key, None)


def _as_date(value):
	if isinstance(value, datetime):
		return value.date()
	if isinstance(value, date):
		return value
	return date.fromisoformat(str(value).split(" ", 1)[0])


def _as_datetime(value):
	if isinstance(value, datetime):
		return value
	return datetime.fromisoformat(str(value))
