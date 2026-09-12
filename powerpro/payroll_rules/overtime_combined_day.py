"""Explicit cash treatment of a holiday overlapping weekly rest."""
from math import isfinite

REVIEW = 'Require review'
SINGLE = 'Single highest premium'
ADDITIVE = 'Additive premiums'
MODES = {REVIEW, SINGLE, ADDITIVE}
FIELD = 'holiday_weekly_rest_mode'
REST_FIELD = 'holiday_weekly_rest_compensatory'
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
    if method == 'Compensatory Rest':
        try: hybrid_cash_calculation(policy, calculation)
        except ValueError as exc: return str(exc)
        return None
    try: cash_kwargs(policy, calculation)
    except ValueError as exc: return str(exc)
    return None


def hybrid_cash_calculation(policy, calculation):
    """Separate holiday money from the weekly-rest entitlement; never pay rest twice."""
    hours = combined_hours(calculation)
    if not hours or not (policy or {}).get(REST_FIELD):
        raise ValueError('Habilite pagar el feriado junto con descanso compensatorio en las reglas de nómina.')
    total = float(calculation.get('verified_hours') or hours)
    if not isfinite(total) or total <= 0 or abs(total-hours) > .0001:
        raise ValueError('La ventana mezcla obligaciones de descanso distintas; revise cada jornada antes de liquidar.')
    result = dict(calculation)
    # The holiday already contains its base and premium. Weekly rest is credited,
    # never converted into another cash premium by the cash-mode setting.
    result.pop('segments', None)
    result.update(holiday_weekly_rest_hours=0, weekly_rest_hours=0,
                  regular_35_hours=0, regular_100_hours=0)
    return result
