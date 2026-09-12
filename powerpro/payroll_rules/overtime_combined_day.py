"""Explicit cash treatment of a holiday overlapping weekly rest."""
from math import isfinite

REVIEW = 'Require review'
SINGLE = 'Single highest premium'
ADDITIVE = 'Additive premiums'
MODES = {REVIEW, SINGLE, ADDITIVE}
FIELD = 'holiday_weekly_rest_mode'
HOURS = 'holiday_weekly_rest_hours'


def combined_hours(calculation):
    calculation = calculation or {}
    if 'segments' in calculation:
        return round(sum(float(r.get('verified_hours') or 0) for r in calculation['segments']
                         if r.get('classification') == 'Legal Holiday on Weekly Rest'), 4)
    return float(calculation.get(HOURS) or 0)


def cash_kwargs(policy, calculation):
    hours = combined_hours(calculation)
    if not hours: return {}
    mode = (policy or {}).get(FIELD) or REVIEW
    if mode not in {SINGLE, ADDITIVE}:
        raise ValueError('Seleccione en las reglas cómo liquidar el feriado que coincide con descanso semanal.')
    holiday = float(policy.get('extraordinary_percent') or 0)
    rest = float(policy.get('weekly_rest_percent') or 0)
    if not isfinite(hours) or hours < 0 or min(holiday, rest) < 100 or not all(map(isfinite, [holiday, rest])):
        raise ValueError('Las horas y los recargos de la coincidencia deben ser válidos.')
    return {HOURS: hours, 'holiday_weekly_rest_percent': holiday + rest if mode == ADDITIVE else max(holiday, rest)}


def settlement_blocker(policy, calculation, method):
    hours = combined_hours(calculation)
    if not hours: return None
    calculation[HOURS] = hours
    try: cash_kwargs(policy, calculation)
    except ValueError as exc: return str(exc)
    if method != 'Cash':
        return ('La coincidencia requiere separar el pago del feriado y el descanso compensatorio; '
                'esta opción de reglas habilita únicamente la liquidación en efectivo.')
    return None
