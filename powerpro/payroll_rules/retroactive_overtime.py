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
