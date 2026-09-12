"""Evidence acceptance independent of Frappe. No synthetic punches or payroll writes."""
from copy import deepcopy
from datetime import timedelta
from powerpro.payroll_rules.overtime import _as_datetime,WorkInterval,_outside_adjacent_portions,_subtract_interval
from powerpro.payroll_rules.overtime_shift_evidence import interpret_shift_punches, captured_window_kind
from powerpro.payroll_rules.overtime_calendar import reconcile_calendar_intervals
from powerpro.payroll_rules.overtime_work_call import derive_reconciliation_snapshot

VERSION='checkin-evidence-v2-actual-week'
EVIDENCE_FIELDS=('evidence_enrolled','evidence_status','evidence_enrolled_by','evidence_enrolled_on','evidence_last_hash','evidence_last_attempt','evidence_retry_after','evidence_issues','evidence_snapshot','evidence_settlement_ready','evidence_auto_settle')
INFORMATIONAL={'direction_reinterpreted','first_last_includes_breaks'}


def evaluate_evidence(*, authorization, rows, shift, contexts, next_windows, now, competing=False,
                      context_complete=True, weekly_before=None, regular_cap=24, night_start=None, night_end=None,observation_window=None):
    start,end=_as_datetime(authorization['start']),_as_datetime(authorization['end'])
    if end<=start or end-start>timedelta(hours=48):raise ValueError('Ventana autorizada inválida.')
    result={'version':VERSION,'state':'Verified','issues':[],'interpretations':[],'source_checkins':deepcopy(rows)}
    def issue(code,severity='review'):
        if not any(r['code']==code for r in result['issues']):result['issues'].append({'code':code,'severity':severity})
    if competing:issue('overlapping_authorization')
    if not context_complete:issue('incomplete_context')
    first=next((c for c in contexts if c['date']==str(start.date())),None)
    if not first or not first.get('shift_start') or not first.get('shift_end'):raise ValueError('Falta turno de referencia.')
    ordinary_start,ordinary_end=_as_datetime(first['shift_start']),_as_datetime(first['shift_end'])
    regular=first['classification']=='Regular Workday'
    session_start=min(ordinary_start,start)
    session_end=max(ordinary_end,end) if regular else end
    if observation_window is not None:
        from powerpro.payroll_rules.overtime_observation_window import normalize_window
        observation_window=normalize_window(observation_window,session_start,session_end)
        session_start,session_end=_as_datetime(observation_window['start']),_as_datetime(observation_window['end'])
    cutoff=session_end+timedelta(minutes=float(shift.get('allow_check_out_after_shift_end_time') or 0))
    if _as_datetime(now)<cutoff:issue('window_not_ended','wait')
    if not shift.get('last_sync_of_checkin') or _as_datetime(shift['last_sync_of_checkin'])<cutoff:issue('sync_incomplete','wait')
    if session_end-session_start>timedelta(hours=24):issue('extended_session_over_24h')
    group=[]
    for raw in sorted(rows,key=lambda r:(_as_datetime(r['time']),str(r.get('name') or ''))):
        stamp=_as_datetime(raw['time'])
        captured=captured_window_kind(raw,authorization['shift'],ordinary_start,ordinary_end,shift)
        # Include documented shift attendance and punches in the authorization.
        # The caller also supplies a bounded late-out tolerance for overrun review.
        in_window=session_start<=stamp<=session_end if observation_window else start<=stamp<=end+timedelta(minutes=float(shift.get('allow_check_out_after_shift_end_time') or 0))
        if not captured and not in_window:continue
        if stamp<session_start-timedelta(minutes=float(shift.get('begin_check_in_before_shift_start_time') or 0)):continue
        if stamp>session_end+timedelta(minutes=float(shift.get('allow_check_out_after_shift_end_time') or 0)):continue
        if raw.get('skip_auto_attendance'):issue('excluded_checkin');continue
        overlaps=[w for w in next_windows if _as_datetime(w['start'])<=stamp<=_as_datetime(w['end'])]
        if overlaps:
            issue('adjacent_shift_overlap' if any(w.get('relation')=='previous' for w in overlaps) else 'next_shift_overlap');continue
        r=deepcopy(raw)
        if captured=='friday_base':
            result['interpretations'].append({'checkin':raw.get('name'),'time':stamp.isoformat(),
                'stored_log_type':raw.get('log_type'),'group':'configured_friday_schedule',
                'captured_shift_end':_as_datetime(raw['shift_end']).isoformat(),
                'scheduled_shift_end':ordinary_end.isoformat()})
        if not captured:
            result['interpretations'].append({'checkin':raw.get('name'),'time':stamp.isoformat(),'stored_log_type':raw.get('log_type'),
                'group':'historical_observation' if observation_window else 'authorized_extension'})
        r.update(shift=authorization['shift'],shift_start=session_start,shift_end=session_end,
                 shift_actual_start=session_start-timedelta(minutes=float(shift.get('begin_check_in_before_shift_start_time') or 0)),
                 shift_actual_end=session_end+timedelta(minutes=float(shift.get('allow_check_out_after_shift_end_time') or 0)),offshift=0)
        group.append(r)
    interpreted=interpret_shift_punches(group,{authorization['shift']:shift})
    result['sessions']=interpreted['sessions']
    for warning in interpreted['issues']:
        issue(warning['code'],'information' if warning['code'] in INFORMATIONAL else 'review')
    if not interpreted['intervals']:issue('missing_punch_pair')
    if result['issues'] and any(i['severity']!='information' for i in result['issues']):
        result['state']='Waiting' if any(i['severity']=='wait' for i in result['issues']) else 'Needs Review'
        return result
    return calculate_evidenced_intervals(result,authorization,interpreted['intervals'],contexts,now,
        weekly_before=weekly_before,regular_cap=regular_cap,night_start=night_start,night_end=night_end)


def calculate_evidenced_intervals(result, authorization, worked, contexts, now, *, weekly_before=None,
                                  regular_cap=24, night_start=None, night_end=None):
    """Shared calendar/snapshot calculation after evidence has been accepted."""
    start,end=_as_datetime(authorization['start']),_as_datetime(authorization['end'])
    rows=result['source_checkins']
    def issue(code):
        result['issues'].append({'code':code,'severity':'review'})
    intervals=[WorkInterval(a,b) for a,b in worked]
    kwargs={}
    if night_start is not None:kwargs['night_start']=night_start
    if night_end is not None:kwargs['night_end']=night_end
    calculation=reconcile_calendar_intervals(authorization_start=start,authorization_end=end,
        maximum_hours=authorization['maximum_hours'],intervals=intervals,contexts=contexts,
        regular_hours_before_by_week=weekly_before,regular_35_percent_cap=regular_cap,**kwargs)
    # An unapproved tail adjacent to this authorization remains reviewable; it is
    # never silently discarded because the authorized maximum caps payment.
    outside=_outside_adjacent_portions(intervals,WorkInterval(start,end))
    for c in contexts:
        if c.get('classification')=='Regular Workday' and c.get('shift_start') and c.get('shift_end'):
            outside=_subtract_interval(outside,WorkInterval(_as_datetime(c['shift_start']),_as_datetime(c['shift_end'])))
    unapproved=[{'start':r.start.isoformat(),'end':r.end.isoformat()} for r in outside]
    calculation.update(source_checkins=deepcopy(rows),warnings=[],unapproved_intervals=unapproved,
        unapproved_hours=round(sum((_as_datetime(r['end'])-_as_datetime(r['start'])).total_seconds()/3600 for r in unapproved),4))
    snapshot=derive_reconciliation_snapshot(authorization_start=start,authorization_end=end,
        maximum_hours=authorization['maximum_hours'],reconciliation=calculation,evaluation_time=now)
    if snapshot['reconciliation_status']!='Completed':issue('worked_authorized_mismatch')
    result.update(calculation=calculation,snapshot=snapshot,worked_intervals=[{'start':a.isoformat(),'end':b.isoformat()} for a,b in worked])
    if any(i['severity']=='review' for i in result['issues']):result['state']='Needs Review'
    return result
