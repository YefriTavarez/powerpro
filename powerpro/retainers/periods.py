"""Calendar periods and stable billing identities (no Frappe dependency)."""

from calendar import monthrange
from datetime import date, datetime
from hashlib import sha256


def period_bounds(anchor, frequency):
    if isinstance(anchor, datetime):
        anchor = anchor.date()
    elif not isinstance(anchor, date):
        anchor = date.fromisoformat(str(anchor))
    last = monthrange(anchor.year, anchor.month)[1]
    if frequency == "Monthly":
        first = 1
    elif frequency == "Bimonthly":
        first, last = (1, 15) if anchor.day <= 15 else (16, last)
    else:
        raise ValueError("Frequency must be Monthly or Bimonthly.")
    return anchor.replace(day=first), anchor.replace(day=last)


def claim_key(identity, period_start, period_end):
    """The identity is the original agreement, retained across amendments."""
    value = "|".join((identity, str(period_start), str(period_end)))
    return sha256(value.encode("utf-8")).hexdigest()
