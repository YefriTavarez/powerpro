"""Work-time diagnostics; never alter earned hours or certify legal compliance.

Profiles are explicit evaluation assumptions. Documentary applicability and
coverage are separate from arithmetic. Calendar weeks/quarters are named in the
result, not silently substituted for an agreed legal reference period.
"""
from datetime import datetime,time,timedelta
from powerpro.payroll_rules.overtime import _as_datetime
from powerpro.payroll_rules.overtime_shift_evidence import union_intervals

VERSION='working-time-controls-v1'
PROFILES={
 'General':(8,44,'147'),
 'Agreed industrial continuous day':(9,44,'157'),
 'Agreed commercial continuous day':(10,44,'157'),
 'Continuous operation':(9,50,'158'),
 'Declared hazardous work':(6,36,'148'),
}


def _intervals(rows):
    pairs=[]
    for row in rows:
        a,b=_as_datetime(row['start']),_as_datetime(row['end'])
        if a.tzinfo or b.tzinfo or b<=a:raise ValueError('Use intervalos positivos en hora local del sitio.')
        pairs.append((a,b))
    return union_intervals(pairs)


def _hours(intervals,start=None,end=None):
    return sum(max((min(b,end) if end else b)-(max(a,start) if start else a),timedelta()).total_seconds() for a,b in intervals)/3600


def evaluate(*,worked_intervals,weekly_intervals,session_complete,weekly_complete,week_start,cutoff,
             profile='General',reference='',break_rule='One hour after four',breaks_observable=True,
             quarter_intervals=(),quarter_start=None,quarter_end=None,quarter_complete=False,
             quarterly_basis='Unclassified',rest_start=None,rest_end=None):
    if profile not in PROFILES:raise ValueError('Seleccione un régimen de jornada implementado.')
    if profile!='General' and not str(reference).strip():raise ValueError('Documente la aplicabilidad del régimen seleccionado.')
    if break_rule not in {'One hour after four','Ninety minutes after five'}:raise ValueError('Seleccione la regla de pausa a evaluar.')
    if quarterly_basis not in {'Unclassified','Extraordinary workload','Other documented cause'}:raise ValueError('Clasifique la causa de prolongación trimestral.')
    work=_intervals(worked_intervals);week=_intervals(weekly_intervals)
    start,stop=_as_datetime(week_start),_as_datetime(cutoff)
    if stop<=start or stop-start>timedelta(days=9):raise ValueError('Ventana semanal inválida.')
    rows=[]
    def add(code,status,observed,limit,unit,article,message,**details):
        rows.append(dict(code=code,status=status,observed=round(observed,4) if observed is not None else None,
            limit=limit,unit=unit,article=article,message=message,**details))
    daily,weekly,article=PROFILES[profile]
    total=_hours(work)
    add('daily_work','Review' if total>daily else ('Within evaluated limit' if session_complete else 'Incomplete'),total,daily,'hours',article,
        'Tiempo de la jornada completa frente al límite del régimen seleccionado; una prolongación exige justificar su supuesto.',scope='complete work session')
    if not session_complete:add('session_evidence','Incomplete',None,None,'','', 'Falta evidencia completa de la jornada; el total observado puede ser parcial.')
    # Split at Monday even when a Sunday extension ends in the following week.
    cursor=datetime.combine(start.date()-timedelta(days=start.weekday()),time.min)
    while cursor<stop:
        end=cursor+timedelta(days=7);a,b=max(cursor,start),min(end,stop)
        hours=_hours(week,a,b)
        add('weekly_work','Review' if hours>weekly else ('Within evaluated limit' if weekly_complete else 'Incomplete'),hours,weekly,'hours',article,
            'Acumulado evidenciado hasta el corte; no equivale a una semana completa ni a autorización para prolongarla.',
            start=a.isoformat(),end=b.isoformat(),week_basis='Monday calendar week')
        cursor=end
    if profile in {'Agreed industrial continuous day','Agreed commercial continuous day','Continuous operation'}:
        add('work_break','Documented regime required',None,None,'minutes','157/158',
            'Este perfil requiere comprobar el acuerdo o funcionamiento continuo; no se presume por el nombre del puesto.')
    elif not session_complete or not breaks_observable:
        add('work_break','Incomplete',None,None,'minutes','157',
            'No hay evidencia suficiente de pausas. Primera entrada y última salida no demuestran descansos intermedios.')
    else:
        maximum,pause=(4,60) if break_rule=='One hour after four' else (5,90)
        block=0.;largest=0.;problems=[]
        for index,(a,b) in enumerate(work):
            block+=(b-a).total_seconds()/3600
            largest=max(largest,block)
            if block>maximum:problems.append({'start':a.isoformat(),'end':b.isoformat(),'continuous_work_hours':round(block,4)})
            if index+1<len(work):
                gap=(work[index+1][0]-b).total_seconds()/60
                if gap>=pause:block=0.
        add('work_break','Review' if problems else 'Within evaluated limit',largest,maximum,'hours','157',
            'Se acumula trabajo entre pausas que alcanzan la duración mínima seleccionada.',minimum_break_minutes=pause,issues=problems)
    if quarter_start and quarter_end:
        a,b=_as_datetime(quarter_start),_as_datetime(quarter_end)
        if b<=a or b-a>timedelta(days=93):raise ValueError('Ventana trimestral inválida.')
        known=_hours(_intervals(quarter_intervals),a,b)
        if quarterly_basis!='Extraordinary workload':status='Applicability review'
        else:status='Review' if known>80 else ('Within evaluated limit' if quarter_complete else 'Incomplete')
        add('quarterly_extension',status,known,80,'hours','155',
            'Horas extra evidenciadas en los orígenes consultados; el límite requiere clasificar la causa y certificar cobertura del período.',
            start=a.isoformat(),end=b.isoformat(),basis=quarterly_basis,coverage_complete=bool(quarter_complete))
    if bool(rest_start)!=bool(rest_end):raise ValueError('Indique inicio y fin del descanso previsto.')
    if rest_start:
        a,b=_as_datetime(rest_start),_as_datetime(rest_end)
        if b<=a:raise ValueError('El descanso debe tener duración positiva.')
        duration=(b-a).total_seconds()/3600;overlap=_hours(_intervals(weekly_intervals+worked_intervals),a,b)
        add('weekly_continuous_rest','Review' if duration<36 or overlap else 'Enjoyment unverified',duration,36,'hours','163',
            'Comprueba duración prevista y trabajo registrado que la interrumpe; ausencia de ponches no prueba disfrute.',
            start=a.isoformat(),end=b.isoformat(),recorded_work_hours=round(overlap,4))
    else:add('weekly_continuous_rest','Incomplete',None,36,'hours','163','Falta identificar la ventana convenida de descanso semanal.')
    return {'version':VERSION,'profile':profile,'reference':reference,'break_rule':break_rule,'controls':rows,
            'compliance_certified':False,'affects_payment':False}
