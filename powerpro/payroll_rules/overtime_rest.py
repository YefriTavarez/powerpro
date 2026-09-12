"""Explicit rest entitlements and schedules under an approved pay policy."""
from datetime import datetime,time,timedelta
from math import isfinite
from powerpro.payroll_rules.overtime import _as_datetime


def rest_entitlement(policy,worked_hours,*,weekly_rest=False):
    if not policy or not policy.get('enable_compensatory'):
        raise ValueError('La política no autoriza descanso compensatorio.')
    hours=float(worked_hours)
    if not isfinite(hours) or hours<=0:raise ValueError('Faltan horas verificadas para el descanso.')
    if weekly_rest:
        credit=float(policy.get('weekly_rest_credit_hours') or 0)
        minimum=float(policy.get('weekly_rest_duration_hours') or 0)
        if not isfinite(credit) or credit<=0 or not isfinite(minimum) or minimum<36:
            raise ValueError('Defina el crédito aprobado y al menos 36 horas continuas para el descanso semanal.')
    else:
        factor=float(policy.get('rest_hours_per_worked_hour') or 0)
        if not isfinite(factor) or factor<1:raise ValueError('Defina al menos una hora de descanso por hora compensada.')
        credit,minimum=hours,hours*factor
    divisor=float(policy.get('hours_per_leave_day') or 0)
    if not isfinite(divisor) or divisor<=0:raise ValueError('Falta la equivalencia aprobada de licencia.')
    return {'credit_hours':credit,'minimum_rest_hours':minimum,'required_leave_days':credit/divisor,
            'weekly_rest':bool(weekly_rest)}


def validate_rest_schedule(start,end,*,work_date,authorization_end,entitlement):
    start,end=_as_datetime(start),_as_datetime(end)
    if end<=start or end-start>timedelta(days=14):raise ValueError('La ventana de descanso debe ser positiva y no superar catorce días.')
    if start<_as_datetime(authorization_end):raise ValueError('El descanso debe comenzar después del trabajo autorizado.')
    if (end-start).total_seconds()/3600+1e-9<entitlement['minimum_rest_hours']:
        raise ValueError('La ventana no alcanza el descanso mínimo aprobado.')
    if entitlement['weekly_rest']:
        date=_as_datetime(str(work_date)).date()
        following=datetime.combine(date-timedelta(days=date.weekday())+timedelta(days=7),time.min)
        if start<following or end>following+timedelta(days=7):
            raise ValueError('El descanso semanal compensatorio debe programarse dentro de la semana siguiente.')
    return {'start':start.isoformat(),'end':end.isoformat(),'hours':(end-start).total_seconds()/3600}
