"""Calendar allocation only: no Frappe imports, IO, payroll creation or writes."""
from calendar import monthrange
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

SPLIT = "50 % en cada quincena"
FIRST = "100 % en la primera quincena"
SECOND = "100 % en la segunda quincena"
MODES = (SPLIT, FIRST, SECOND)


def as_date(value):
    if isinstance(value, date):
        return date(value.year, value.month, value.day)
    return date.fromisoformat(str(value)[:10])


def money(value, precision=2):
    if not isinstance(precision, int) or not 0 <= precision <= 6:
        raise ValueError("Precisión monetaria inválida.")
    try:
        amount = Decimal(str(value or 0))
        if not amount.is_finite() or amount < 0:
            raise ValueError("El importe debe ser finito y no negativo.")
        return amount.quantize(Decimal(1).scaleb(-precision), rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError("Importe monetario inválido.") from exc


def allocation(amount, mode, start, end, frequency, *, second_day=16, precision=2):
    """Return the monthly base assigned to a complete payroll period.

    A consolidated Monthly receipt includes the monthly amount once. Existing
    salary-component rules (e.g. payment-day proration) remain the engine's job.
    No catch-up charge is moved from an unpaid first half into the second half.
    """
    if mode not in MODES:
        raise ValueError("Seleccione una aplicación en nómina válida.")
    start, end = as_date(start), as_date(end)
    if not isinstance(second_day, int) or not 2 <= second_day <= 28:
        raise ValueError("Revise el inicio de la segunda quincena.")
    first = start.replace(day=1)
    last = start.replace(day=monthrange(start.year, start.month)[1])
    second = start.replace(day=second_day)
    first_end = start.replace(day=second_day - 1)
    monthly = money(amount, precision)
    if frequency == "Monthly" and start == first and end == last:
        return monthly
    if frequency != "Bimonthly" or (start, end) not in ((first, first_end), (second, last)):
        raise ValueError("La aplicación recurrente requiere un mes o una quincena completos del calendario configurado.")
    first_amount = monthly if mode == FIRST else Decimal(0) if mode == SECOND else money(monthly / 2, precision)
    return first_amount if start == first else monthly - first_amount
