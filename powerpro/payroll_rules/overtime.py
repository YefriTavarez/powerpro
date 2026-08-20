"""Pure overtime reconciliation rules for Dominican payroll.

The functions in this module perform no database access. Check-ins are evidence;
they never authorize overtime by themselves. A caller must supply an approved
window and maximum before any payable or compensatory hours can be returned.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta


REGULAR_DAY = "Regular Workday"
LEGAL_HOLIDAY = "Legal Holiday"
WEEKLY_REST = "Weekly Rest"
HOLIDAY_ON_WEEKLY_REST = "Legal Holiday on Weekly Rest"

START_ACTIONS = {"IN", "INICIO JORNADA", "FIN BREAK"}
STOP_ACTIONS = {"OUT", "INICIO BREAK", "FIN JORNADA"}


@dataclass(frozen=True)
class WorkInterval:
    start: datetime
    end: datetime

    @property
    def hours(self):
        return max((self.end - self.start).total_seconds() / 3600, 0.0)


def classify_workday(*, is_shift_workday, has_legal_holiday):
    """Classify a date without stacking weekly-rest and holiday premiums."""
    if has_legal_holiday and not is_shift_workday:
        return HOLIDAY_ON_WEEKLY_REST
    if has_legal_holiday:
        return LEGAL_HOLIDAY
    if not is_shift_workday:
        return WEEKLY_REST
    return REGULAR_DAY


def holiday_list_covers(work_date, from_date, to_date):
    """Return whether a dated Holiday List safely covers the work date."""
    if not from_date or not to_date:
        return False
    work_date = _as_date(work_date)
    return _as_date(from_date) <= work_date <= _as_date(to_date)


def get_regular_35_percent_cap(weekly_expected_hours, weekly_total_threshold):
    """Return ordinary overtime hours available before the +100% band.

    DGII Payroll Settings stores the total weekly-hours threshold at which
    extraordinary overtime begins. For example, a 44-hour workweek and a
    68-hour threshold permit 24 hours in the +35% band.
    """
    expected = float(weekly_expected_hours or 0)
    threshold = float(weekly_total_threshold or 0)
    if expected <= 0 or threshold <= expected:
        raise ValueError(
            "Weekly total threshold must be greater than weekly expected hours"
        )
    return threshold - expected


def get_shift_window(work_date, start_time, end_time, friday_end_time=None):
    """Build one scheduled shift window, including Friday and overnight rules."""
    if isinstance(work_date, datetime):
        work_date = work_date.date()
    elif not isinstance(work_date, date):
        work_date = date.fromisoformat(str(work_date))

    start_clock = coerce_time(start_time)
    effective_end = friday_end_time if work_date.weekday() == 4 and friday_end_time else end_time
    end_clock = coerce_time(effective_end)
    if start_clock is None or end_clock is None:
        return None, None

    start = datetime.combine(work_date, start_clock)
    end = datetime.combine(work_date, end_clock)
    if end <= start:
        end += timedelta(days=1)
    return start, end


def coerce_time(value, default=None):
    """Normalize Frappe Time values without requiring Frappe imports."""
    if value is None or value == "":
        return default
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


def reconcile_authorized_overtime(
    *,
    authorization_start,
    authorization_end,
    maximum_hours,
    checkins,
    day_classification,
    shift_start=None,
    shift_end=None,
    approved_regular_overtime_before=0,
    regular_35_percent_cap=24,
    night_start=time(21, 0),
    night_end=time(7, 0),
):
    """Return verified hours within an already-approved authorization window.

    On regular workdays, only verified time outside the scheduled shift counts.
    On legal holidays and weekly rest days, all verified time in the approved
    window counts, but it is kept in a separate category for settlement.
    """
    authorization_start = _as_datetime(authorization_start)
    authorization_end = _as_datetime(authorization_end)
    maximum_hours = float(maximum_hours or 0)
    if authorization_end <= authorization_start:
        raise ValueError("Authorization end must be after its start")
    if maximum_hours <= 0:
        raise ValueError("Maximum authorized hours must be greater than zero")

    intervals, warnings = build_work_intervals(checkins)
    intervals = _intersections(
        intervals,
        WorkInterval(authorization_start, authorization_end),
    )

    if day_classification == REGULAR_DAY:
        if not shift_start or not shift_end:
            raise ValueError("A regular workday requires scheduled shift times")
        scheduled = WorkInterval(_as_datetime(shift_start), _as_datetime(shift_end))
        intervals = _subtract_interval(intervals, scheduled)

    intervals = _cap_intervals(intervals, maximum_hours)
    verified_hours = _round_hours(sum(interval.hours for interval in intervals))
    night_hours = _round_hours(
        sum(_night_overlap_hours(interval, night_start, night_end) for interval in intervals)
    )

    result = {
        "classification": day_classification,
        "verified_hours": verified_hours,
        "regular_35_hours": 0.0,
        "regular_100_hours": 0.0,
        "holiday_100_hours": 0.0,
        "weekly_rest_hours": 0.0,
        "night_hours": night_hours,
        "warnings": warnings,
        "intervals": [
            {"start": interval.start.isoformat(), "end": interval.end.isoformat()}
            for interval in intervals
        ],
    }

    if day_classification == REGULAR_DAY:
        remaining_35 = max(
            float(regular_35_percent_cap) - float(approved_regular_overtime_before or 0),
            0.0,
        )
        result["regular_35_hours"] = _round_hours(min(verified_hours, remaining_35))
        result["regular_100_hours"] = _round_hours(
            verified_hours - result["regular_35_hours"]
        )
    elif day_classification in (LEGAL_HOLIDAY, HOLIDAY_ON_WEEKLY_REST):
        result["holiday_100_hours"] = verified_hours
    elif day_classification == WEEKLY_REST:
        result["weekly_rest_hours"] = verified_hours
    else:
        raise ValueError(f"Unsupported day classification: {day_classification}")

    return result


def build_work_intervals(checkins):
    """Build worked intervals from check-in actions without inventing punches."""
    normalized = sorted(
        (
            {
                "time": _as_datetime(row["time"]),
                "action": _action(row),
            }
            for row in checkins
            if row.get("time")
        ),
        key=lambda row: row["time"],
    )
    intervals = []
    warnings = []
    opened_at = None

    for row in normalized:
        action = row["action"]
        if action in START_ACTIONS:
            if opened_at is not None:
                warnings.append(f'Duplicate start punch at {row["time"].isoformat()}')
                opened_at = row["time"]
                continue
            opened_at = row["time"]
        elif action in STOP_ACTIONS:
            if opened_at is None:
                warnings.append(f'Orphan stop punch at {row["time"].isoformat()}')
                continue
            if row["time"] > opened_at:
                intervals.append(WorkInterval(opened_at, row["time"]))
            else:
                warnings.append(f'Invalid punch pair ending {row["time"].isoformat()}')
            opened_at = None
        elif action:
            warnings.append(
                f'Unrecognized check-in action "{action}" at {row["time"].isoformat()}'
            )

    if opened_at is not None:
        warnings.append(f'Open work interval beginning {opened_at.isoformat()}')

    return intervals, warnings


def _action(row):
    value = str(row.get("accion") or row.get("log_type") or "").strip().upper()
    return " ".join(value.split())


def _intersections(intervals, boundary):
    result = []
    for interval in intervals:
        start = max(interval.start, boundary.start)
        end = min(interval.end, boundary.end)
        if end > start:
            result.append(WorkInterval(start, end))
    return result


def _subtract_interval(intervals, excluded):
    result = []
    for interval in intervals:
        if interval.end <= excluded.start or interval.start >= excluded.end:
            result.append(interval)
            continue
        if interval.start < excluded.start:
            result.append(WorkInterval(interval.start, excluded.start))
        if interval.end > excluded.end:
            result.append(WorkInterval(excluded.end, interval.end))
    return result


def _cap_intervals(intervals, maximum_hours):
    remaining = float(maximum_hours)
    result = []
    for interval in intervals:
        if remaining <= 0:
            break
        hours = interval.hours
        if hours <= remaining:
            result.append(interval)
            remaining -= hours
        else:
            result.append(WorkInterval(interval.start, interval.start + timedelta(hours=remaining)))
            remaining = 0
    return result


def _night_overlap_hours(interval, night_start, night_end):
    total = 0.0
    day = interval.start.date() - timedelta(days=1)
    last_day = interval.end.date()
    while day <= last_day:
        start = datetime.combine(day, night_start)
        end_day = day if night_end > night_start else day + timedelta(days=1)
        end = datetime.combine(end_day, night_end)
        overlap_start = max(interval.start, start)
        overlap_end = min(interval.end, end)
        if overlap_end > overlap_start:
            total += (overlap_end - overlap_start).total_seconds() / 3600
        day += timedelta(days=1)
    return total


def _as_datetime(value):
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def _as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _round_hours(value):
    return round(float(value or 0), 4)
