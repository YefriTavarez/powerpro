"""Pure rules. Amounts are full monthly entitlements, never attendance-prorated."""
from calendar import monthrange
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib

FIELDS = {
    "incentivo_especial": "Incentivo Especial",
    "asignacion_transporte": "Asignación para Transporte",
    "asignacion_combustible": "Asignación para Combustible",
    "asignacion_mantenimiento_vehiculo": "Asignación para Mantenimiento de Vehículo",
}


def day(value):
    return date.fromisoformat(str(value)[:10])


def money(value, precision=2):
    try:
        amount = Decimal(str(value if value is not None else 0))
        if not amount.is_finite() or amount < 0:
            raise ValueError("Los complementos deben ser importes finitos no negativos.")
        return amount.quantize(Decimal(1).scaleb(-precision), rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError) as exc:
        raise ValueError("Importe de complemento inválido.") from exc


def period_amount(monthly, frequency, start, end, second_day=16, precision=2):
    start, end = day(start), day(end)
    last = monthrange(start.year, start.month)[1]
    if (start.year, start.month) != (end.year, end.month):
        raise ValueError("Los complementos requieren un período dentro del mismo mes.")
    amount = money(monthly, precision)
    if frequency == "Monthly" and start.day == 1 and end.day == last:
        return amount
    if frequency == "Bimonthly" and second_day in (15, 16):
        first = money(amount / 2, precision)
        if start.day == 1 and end.day == second_day - 1:
            return first
        if start.day == second_day and end.day == last:
            return amount - first  # halves add back to the exact monthly amount
    raise ValueError("Período incompatible con los complementos: use mes completo o quincena configurada.")


def applies(row, start, end):
    """Exactly match HRMS v15's additional-salary selection (recurring at end date)."""
    if row.get("docstatus") != 1 or row.get("disabled"):
        return False
    if row.get("is_recurring"):
        return bool(row.get("from_date") and row.get("to_date") and
                    day(row["from_date"]) <= day(end) <= day(row["to_date"]))
    return bool(row.get("payroll_date") and day(start) <= day(row["payroll_date"]) <= day(end))


def overlaps(start, end, other_start, other_end):
    return day(start) <= day(other_end) and day(other_start) <= day(end)


def key(company, employee, field, start, end):
    return hashlib.sha256("\0".join(map(str, (company, employee, field, day(start), day(end)))).encode()).hexdigest()


def resolve(expected, candidates, coverage_names=(), independent_names=(), owned_key=None):
    """Never infer ownership from amount or component; caller supplies explicit classification."""
    expected = money(expected, 4)
    coverage, independent = set(coverage_names), set(independent_names)
    fixed = []
    for row in candidates:
        if row.get("overwrite_salary_structure_amount"):
            raise ValueError(f"{row['name']}: reemplaza el componente salarial; concilie antes de continuar.")
        owned = bool(owned_key and row.get("pp_supplement_key") == owned_key)
        if owned or row["name"] in coverage:
            fixed.append(row)
        elif row["name"] in independent or row.get("pp_supplement_treatment") == "Independent":
            if row.get("pp_supplement_key"):
                raise ValueError("Un complemento automático no puede clasificarse como pago independiente.")
        else:
            raise ValueError(f"{row['name']}: adicional sin clasificar para un componente de complemento fijo.")
    if len(fixed) > 1:
        raise ValueError("Hay más de un Additional Salary cubriendo el mismo complemento y período.")
    if fixed:
        if money(fixed[0]["amount"], 4) != expected:
            raise ValueError(f"{fixed[0]['name']}: el importe existente no coincide con el complemento del período.")
        return fixed[0]["name"]
    return None
