"""Calendar-segmented calculation for comparison only; no payroll writes.

This first iteration retains the existing premium bands and night-overlap rule.
It does not decide the pending full-night-shift or combined-premium policies.
"""
from datetime import datetime, time, timedelta
from math import isfinite

from powerpro.payroll_rules.overtime import (
    HOLIDAY_ON_WEEKLY_REST, LEGAL_HOLIDAY, REGULAR_DAY, WEEKLY_REST,
    WorkInterval, _as_datetime, _intersections, _night_overlap_hours,
    _round_hours, _subtract_interval,
)

HOUR_FIELDS = (
    "verified_hours", "regular_35_hours", "regular_100_hours",
    "holiday_100_hours", "weekly_rest_hours", "night_hours",
)
CLASSIFICATIONS = {REGULAR_DAY, LEGAL_HOLIDAY, WEEKLY_REST, HOLIDAY_ON_WEEKLY_REST}


def calendar_dates(start, end):
    """Dates touched by [start, end); midnight at the end belongs to no new day."""
    start, end = _as_datetime(start), _as_datetime(end)
    if end <= start:
        raise ValueError("El fin debe ser posterior al inicio.")
    if end - start > timedelta(days=2):
        raise ValueError("La comparación admite ventanas de hasta 48 horas.")
    day = start.date()
    while datetime.combine(day, time.min) < end:
        yield day
        day += timedelta(days=1)


def reconcile_calendar_intervals(
    *, authorization_start, authorization_end, maximum_hours, intervals,
    contexts, regular_hours_before_by_week=None, regular_35_percent_cap=24,
    night_start=time(21), night_end=time(7),
):
    start, end = _as_datetime(authorization_start), _as_datetime(authorization_end)
    days = list(calendar_dates(start, end))
    maximum_hours, regular_35_percent_cap = float(maximum_hours), float(regular_35_percent_cap)
    if not isfinite(maximum_hours) or maximum_hours <= 0:
        raise ValueError("El máximo autorizado debe ser positivo y finito.")
    if not isfinite(regular_35_percent_cap) or regular_35_percent_cap <= 0:
        raise ValueError("La banda semanal debe ser positiva y finita.")
    intervals = sorted(intervals, key=lambda row: row.start)
    for index, row in enumerate(intervals):
        if row.end <= row.start or (index and row.start < intervals[index - 1].end):
            raise ValueError("Los intervalos deben ser válidos y no superponerse.")
    by_date = {str(row["date"]): row for row in contexts}
    for day in days:
        context = by_date.get(str(day))
        if not context or not context.get("holiday_list_covers_work_date"):
            raise ValueError(f"El calendario no cubre la fecha {day}.")
        if context.get("classification") not in CLASSIFICATIONS:
            raise ValueError(f"Clasificación de día no admitida: {day}.")
        if context["classification"] == REGULAR_DAY and not (
            context.get("shift_start") and context.get("shift_end")
        ):
            raise ValueError(f"Falta el horario ordinario de {day}.")

    candidates = []
    for day in days:
        context = by_date[str(day)]
        boundary = WorkInterval(max(start, datetime.combine(day, time.min)),
                                min(end, datetime.combine(day + timedelta(days=1), time.min)))
        pieces = _intersections(intervals, boundary)
        if context["classification"] == REGULAR_DAY:
            # Include a previous ordinary night shift that continues into this day.
            for shift_day in (day - timedelta(days=1), day):
                schedule = by_date.get(str(shift_day))
                if schedule and schedule.get("classification") == REGULAR_DAY:
                    if not schedule.get("shift_start") or not schedule.get("shift_end"):
                        raise ValueError(f"Falta el horario ordinario de {shift_day}.")
                    ordinary = WorkInterval(_as_datetime(schedule["shift_start"]),
                                            _as_datetime(schedule["shift_end"]))
                    if ordinary.end <= ordinary.start:
                        raise ValueError("El horario ordinario no es válido.")
                    pieces = _subtract_interval(pieces, ordinary)
        candidates.extend((piece, day, context) for piece in pieces)

    remaining = maximum_hours
    used_by_week = {}
    for key, value in (regular_hours_before_by_week or {}).items():
        value = float(value)
        if not isfinite(value) or value < 0:
            raise ValueError("El acumulado semanal debe ser no negativo y finito.")
        used_by_week[str(key)] = value
    result = {field: 0.0 for field in HOUR_FIELDS}
    segments = []
    for piece, day, context in candidates:
        if remaining <= 0:
            break
        if piece.hours > remaining:
            piece = WorkInterval(piece.start, piece.start + timedelta(hours=remaining))
        hours = piece.hours
        remaining = max(remaining - hours, 0)
        week = str(day - timedelta(days=day.weekday()))
        segment = {field: 0.0 for field in HOUR_FIELDS}
        segment["verified_hours"] = hours
        segment["night_hours"] = _night_overlap_hours(piece, night_start, night_end)
        classification = context["classification"]
        if classification == REGULAR_DAY:
            used = used_by_week.get(week, 0)
            segment["regular_35_hours"] = min(hours, max(regular_35_percent_cap - used, 0))
            segment["regular_100_hours"] = hours - segment["regular_35_hours"]
            used_by_week[week] = used + hours
        elif classification in {LEGAL_HOLIDAY, HOLIDAY_ON_WEEKLY_REST}:
            segment["holiday_100_hours"] = hours
        else:
            segment["weekly_rest_hours"] = hours
        for field in HOUR_FIELDS:
            result[field] += segment[field]
            segment[field] = _round_hours(segment[field])
        segments.append({**segment, "date": str(day), "week_start": week,
                         "classification": classification,
                         "start": piece.start.isoformat(), "end": piece.end.isoformat()})

    result = {field: _round_hours(value) for field, value in result.items()}
    result.update({"segments": segments,
                   "intervals": [{"start": row["start"], "end": row["end"]} for row in segments],
                   "eligible_hours_before_cap": _round_hours(sum(row[0].hours for row in candidates)),
                   "excluded_by_maximum_hours": _round_hours(max(sum(row[0].hours for row in candidates) - maximum_hours, 0))})
    return result
