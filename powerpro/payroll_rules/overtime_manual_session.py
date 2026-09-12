"""Explicit complete-session HR evidence; never manufactures Employee Checkins."""
from copy import deepcopy
from datetime import timedelta
from powerpro.payroll_rules.overtime import _as_datetime
from powerpro.payroll_rules.overtime_evidence import calculate_evidenced_intervals

KIND = 'Manual Full Session'


def validate_manual_intervals(declaration,lower,upper,now):
    """Validate physical declared intervals without invoking financial calculation."""
    if not isinstance(declaration,dict) or declaration.get('full_session') is not True:
        raise ValueError('Confirme que declara toda la jornada, excluyendo las pausas no trabajadas.')
    if not str(declaration.get('reference') or '').strip():
        raise ValueError('Indique la referencia que sustenta la jornada declarada.')
    entries=declaration.get('intervals')
    if not isinstance(entries,list) or not 1<=len(entries)<=48:raise ValueError('Declare entre uno y 48 intervalos de la jornada completa.')
    if upper-lower>timedelta(hours=24):raise ValueError('La jornada declarada no puede exceder 24 horas.')
    if _as_datetime(now)<upper:raise ValueError('La jornada aún no ha terminado.')
    worked=[]
    for row in entries:
        if not isinstance(row,dict) or not row.get('start') or not row.get('end'):raise ValueError('Cada intervalo requiere inicio y fin.')
        a,b=_as_datetime(row['start']),_as_datetime(row['end'])
        if a.tzinfo or b.tzinfo:raise ValueError('Use la hora local del sitio sin sufijo de zona horaria.')
        if b<=a or a<lower or b>upper:raise ValueError('Los intervalos deben ser positivos y estar dentro de la jornada y prolongación documentadas.')
        worked.append((a,b))
    worked.sort()
    if any(b[0]<a[1] for a,b in zip(worked,worked[1:])):raise ValueError('Los intervalos declarados no pueden superponerse.')
    return worked


def evaluate_manual_session(*, declaration, authorization, rows, contexts, now, competing=False, observation_window=None,**kwargs):
    start,end=_as_datetime(authorization['start']),_as_datetime(authorization['end'])
    context=next((r for r in contexts if r['date']==str(start.date())),None)
    if not context:raise ValueError('Falta el turno de la jornada.')
    shift_start,shift_end=_as_datetime(context['shift_start']),_as_datetime(context['shift_end'])
    lower,upper=min(start,shift_start),max(end,shift_end)
    if observation_window is not None:
        from powerpro.payroll_rules.overtime_observation_window import normalize_window
        observation_window=normalize_window(observation_window,lower,upper)
        lower,upper=_as_datetime(observation_window['start']),_as_datetime(observation_window['end'])
    worked=validate_manual_intervals(declaration,lower,upper,now)
    result={'version':'manual-full-session-v1','state':'Verified','issues':[],
        'source_checkins':deepcopy(rows),'interpretations':[],
        'sessions':[{'shift':authorization['shift'],'shift_start':str(shift_start),'shift_end':str(shift_end),
                     'checkins':[r['name'] for r in rows]}],
        'certified_sessions':[{'shift':authorization['shift'],'start':str(shift_start),'end':str(shift_end)}],
        'manual_declaration':deepcopy(declaration)}
    if competing:result['issues'].append({'code':'overlapping_authorization','severity':'review'})
    return calculate_evidenced_intervals(result,authorization,worked,contexts,now,**kwargs)
