"""Validation of manager-certified attendance; no database access."""
from datetime import datetime


def normalize_intervals(rows, *, authorization_start, authorization_end, now):
    """Require completed, nonoverlapping intervals for this approved work window."""
    def stamp(value):
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
        if parsed.tzinfo is not None:
            raise ValueError("Enter times in the site's local timezone without a timezone suffix.")
        return parsed

    start, end, now = map(stamp, (authorization_start, authorization_end, now))
    if now < end:
        raise ValueError("The authorized overtime window has not ended yet.")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 24:
        raise ValueError("Enter between 1 and 24 worked intervals, excluding breaks.")
    intervals = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("start") or not row.get("end"):
            raise ValueError("Each worked interval requires a start and end.")
        a, b = stamp(row["start"]), stamp(row["end"])
        if b <= a:
            raise ValueError("Worked interval end must be after its start.")
        if b > now:
            raise ValueError("Worked intervals cannot end in the future.")
        if a >= end or b <= start:
            raise ValueError("Each worked interval must overlap this authorization's window.")
        intervals.append((a, b))
    intervals.sort()
    for previous, current in zip(intervals, intervals[1:]):
        if current[0] < previous[1]:
            raise ValueError("Worked intervals must not overlap.")
    return [{"start": a.isoformat(), "end": b.isoformat()} for a, b in intervals]


def verification_roles(value):
    return {line.strip() for line in (value or "").splitlines() if line.strip()}
