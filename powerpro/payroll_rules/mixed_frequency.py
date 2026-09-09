"""Period rules for including monthly employees in a second-quincena run."""

from calendar import monthrange
from datetime import date


def as_date(value):
    return date.fromisoformat(str(value)[:10])


def is_second_quincena(frequency, start, end, timesheet=False):
    if frequency != "Bimonthly" or timesheet or not start or not end:
        return False
    start, end = as_date(start), as_date(end)
    # Match PowerPro's mid_month_start boundary, but only close a complete month.
    return (
        start.year == end.year and start.month == end.month
        and 15 <= start.day <= 16
        and end.day == monthrange(end.year, end.month)[1]
    )


def salary_period(frequency, start, end):
    start, end = as_date(start), as_date(end)
    if frequency == "Monthly":
        start = end.replace(day=1)
    return {"payroll_frequency": frequency, "start_date": start, "end_date": end}


def periods_overlap(start, end, other_start, other_end):
    return as_date(start) <= as_date(other_end) and as_date(other_start) <= as_date(end)
