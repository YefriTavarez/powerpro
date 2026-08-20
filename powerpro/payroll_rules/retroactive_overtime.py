"""Pure guardrails for the temporary retroactive-overtime exception path."""

from datetime import date, datetime


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
