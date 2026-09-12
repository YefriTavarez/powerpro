"""Versioned supported payroll rules; approval is supplied by the site controller."""
from datetime import time
from math import isfinite

from powerpro.payroll_rules.overtime import WorkInterval,_as_datetime,_night_overlap_hours

VERSION='overtime-pay-policy-v1'
FIELDS=('name','company','valid_from','valid_until','approval_reference','approved_by','approved_on',
        'weekly_threshold','regular_percent','extraordinary_percent','night_percent',
        'night_basis','premium_combination','weekly_rest_cash','weekly_rest_percent',
        'enable_compensatory','leave_type','hours_per_leave_day','leave_increment',
        'rest_hours_per_worked_hour','weekly_rest_duration_hours','weekly_rest_credit_hours')


def validate_policy(policy):
    from powerpro.payroll_rules.overtime_combined_day import FIELD, MODES, REVIEW
    if (policy.get(FIELD) or REVIEW) not in MODES:
        raise ValueError('Seleccione una regla admitida para feriado y descanso semanal.')
    if not policy.get('company') or not policy.get('valid_from') or not policy.get('valid_until'):
        raise ValueError('Indique empresa y vigencia de la política.')
    if _as_datetime(str(policy['valid_until'])) < _as_datetime(str(policy['valid_from'])):
        raise ValueError('La fecha final de vigencia debe ser posterior o igual al inicio.')
    if not str(policy.get('approval_reference') or '').strip():
        raise ValueError('Documente la aprobación de estas reglas y sus ejemplos de cálculo.')
    for key,minimum in [('regular_percent',35),('extraordinary_percent',100),('night_percent',15),('weekly_rest_percent',100)]:
        value=float(policy.get(key) or 0)
        if not isfinite(value) or value<minimum:
            raise ValueError(f'{key}: el porcentaje no puede ser inferior a {minimum}.')
    threshold=float(policy.get('weekly_threshold') or 0)
    if not isfinite(threshold) or not 0<threshold<=68:
        raise ValueError('El umbral semanal debe ser positivo y no superar 68 horas.')
    if policy.get('night_basis') not in {'Clock overlap','Whole nocturnal session'}:
        raise ValueError('Seleccione expresamente la regla de nocturnidad aprobada.')
    if policy.get('premium_combination')!='Additive on base hour':
        raise ValueError('La combinación de recargos debe tener una regla implementada y aprobada.')
    if policy.get('enable_compensatory'):
        if not policy.get('leave_type'):
            raise ValueError('Indique el tipo de licencia del descanso compensatorio.')
        for field in ['hours_per_leave_day','leave_increment']:
            value=float(policy.get(field) or 0)
            if not isfinite(value) or value<=0:raise ValueError(f'{field} debe ser positivo y finito.')
        factor=float(policy.get('rest_hours_per_worked_hour') or 0)
        if not isfinite(factor) or factor<1:raise ValueError('Defina al menos una hora de descanso por hora compensada.')
        if float(policy['leave_increment']) not in {.5,1}:
            raise ValueError('La licencia nativa admite incrementos de medio día o día completo en esta versión.')


def classify_night_session(worked_intervals, overtime_intervals, *, basis):
    """Classify the complete evidenced session, then apportion its premium.

No rounding before the three-hour boundary. The session grouping comes from
the shift/evidence engine; breaks are not counted as work here.
    """
    worked=[WorkInterval(_as_datetime(r['start']),_as_datetime(r['end'])) for r in worked_intervals]
    overtime=[WorkInterval(_as_datetime(r['start']),_as_datetime(r['end'])) for r in overtime_intervals]
    if basis not in {'Clock overlap','Whole nocturnal session'}:raise ValueError('Regla nocturna no soportada.')
    for collection in [worked,overtime]:
        collection.sort(key=lambda r:r.start)
        if any(r.end<=r.start for r in collection) or any(b.start<a.end for a,b in zip(collection,collection[1:])):
            raise ValueError('Los intervalos deben ser positivos y no superponerse.')
    for extra in overtime:
        seconds=sum(max((min(extra.end,r.end)-max(extra.start,r.start)).total_seconds(),0) for r in worked)
        if abs(seconds-(extra.end-extra.start).total_seconds())>.000001:
            raise ValueError('Las horas extra deben estar contenidas en la jornada evidenciada.')
    total=sum(r.hours for r in worked)
    night=sum(_night_overlap_hours(r,time(21),time(7)) for r in worked)
    classification='Nocturna' if night>=3 else ('Mixta' if night else 'Diurna')
    full=basis=='Whole nocturnal session' and classification=='Nocturna'
    premium_total=total if full else night
    premium_ot=sum(r.hours if full else _night_overlap_hours(r,time(21),time(7)) for r in overtime)
    if premium_ot>premium_total+.000001:raise ValueError('Los intervalos extra exceden la evidencia de jornada.')
    return {'classification':classification,'worked_hours':round(total,4),'clock_night_hours':round(night,4),
            'premium_hours':round(premium_total,4),'overtime_premium_hours':round(premium_ot,4),
            'ordinary_premium_hours':round(max(premium_total-premium_ot,0),4),'basis':basis}


def rates(policy):
    return {'regular_overtime_percent':policy['regular_percent'],
            'extraordinary_overtime_percent':policy['extraordinary_percent'],
            'night_hours_percent':policy['night_percent']}
