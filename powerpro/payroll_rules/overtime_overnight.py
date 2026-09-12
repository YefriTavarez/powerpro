"""Authorization-aware overnight grouping, preview only; never edits punches."""
from copy import deepcopy
from datetime import timedelta
from powerpro.payroll_rules.overtime import _as_datetime
from powerpro.payroll_rules.overtime_shift_evidence import interpret_shift_punches


def compare_overnight(*, authorization, checkins, policies, next_windows, now, context_complete=False, competing=False):
    start, end = _as_datetime(authorization['start']), _as_datetime(authorization['end'])
    if end <= start or end-start > timedelta(hours=48): raise ValueError('Ventana autorizada inválida.')
    result = {'applicable': end.date()>start.date(), 'read_only':True, 'settlement_eligible':False,
              'interpretations':[], 'issues':[], 'sessions':[], 'intervals':[], 'coverage_blockers':[]}
    if not result['applicable']: return result
    def block(code):
        if code not in result['coverage_blockers']:result['coverage_blockers'].append(code)
    if not context_complete:block('incomplete_shift_context')
    if _as_datetime(now) < end:block('authorization_not_ended')
    if competing:block('overlapping_authorizations')
    policy=policies.get(authorization.get('shift'))
    if not policy:block('missing_shift_policy')
    elif not policy.get('last_sync_of_checkin') or _as_datetime(policy['last_sync_of_checkin']) < end:
        block('sync_not_confirmed')
    rows=sorted(checkins,key=lambda r:(_as_datetime(r['time']),str(r.get('name') or '')))
    eligible=[]
    for row in rows:
        if row.get('skip_auto_attendance'):
            if start.date() <= _as_datetime(row['time']).date() <= end.date():block('excluded_checkins')
        else:eligible.append(row)
    # Anchor to a captured same-day ordinary shift; do not invent a start punch
    # from the authorization or from today's default shift.
    anchors={(_as_datetime(r['shift_start']),_as_datetime(r['shift_end'])) for r in eligible
             if r.get('shift')==authorization.get('shift') and r.get('shift_start') and r.get('shift_end')
             and _as_datetime(r['shift_start']).date()==start.date()
             and _as_datetime(r['shift_start']) <= start and _as_datetime(r['shift_end']) <= start}
    if not anchors:
        block('missing_captured_anchor');return result
    anchor_start,anchor_end=max(anchors,key=lambda pair:pair[1])
    if anchor_end <= anchor_start or end-anchor_start > timedelta(hours=24):
        block('extended_session_over_24h');return result
    group=[]
    for row in eligible:
        stamp=_as_datetime(row['time'])
        if stamp > end:continue
        is_anchor=(row.get('shift')==authorization.get('shift') and row.get('shift_start') and row.get('shift_end')
                   and _as_datetime(row['shift_start'])==anchor_start and _as_datetime(row['shift_end'])==anchor_end)
        is_extension=anchor_end <= stamp <= end
        if not is_anchor and not is_extension:continue
        conflicts=[w for w in next_windows if _as_datetime(w['start'])<=stamp<=_as_datetime(w['end'])]
        if is_extension and conflicts:
            block('next_shift_overlap')
            result['interpretations'].append({'checkin':row.get('name'),'time':stamp.isoformat(),
                'stored_log_type':row.get('log_type'),'interpretation':'Needs Review','competing_shifts':[w['shift'] for w in conflicts]})
            continue
        copied=deepcopy(row)
        # This group exists only in memory. All original source rows remain intact.
        copied.update(shift=authorization['shift'],shift_start=anchor_start,shift_end=anchor_end,
                      shift_actual_start=min(anchor_start,_as_datetime(group[0]['time']) if group else stamp),
                      shift_actual_end=end,offshift=0)
        group.append(copied)
        if is_extension and not is_anchor:
            result['interpretations'].append({'checkin':row.get('name'),'time':stamp.isoformat(),
                'stored_log_type':row.get('log_type'),'interpretation':'Previous authorized session','competing_shifts':[]})
    if competing or not context_complete:
        # Without knowledge of competing assignments/authorizations, never move a
        # punch away from its recorded session even for provisional hour totals.
        for item in result['interpretations']:item['interpretation']='Needs Review'
        return result
    interpreted=interpret_shift_punches(group,policies)
    result['sessions']=interpreted['sessions'];result['issues']=interpreted['issues']
    if interpreted['issues']:block('punch_sequence_requires_review')
    if not group or max(_as_datetime(r['time']) for r in group) < start or not interpreted['intervals']:
        block('missing_worked_interval')
    result['intervals']=[{'start':a.isoformat(),'end':b.isoformat()} for a,b in interpreted['intervals']]
    if result['coverage_blockers']:result['status']='Needs Review'
    else:result['status']='Provisional'
    return result
