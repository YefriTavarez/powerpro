"""Bounded, internal weekly evidence loader for the enrolled reconciliation service."""
from datetime import datetime,time,timedelta

import frappe
from frappe.utils import get_datetime,getdate
from powerpro.controllers.overtime import _reconciliation_rows,get_schedule_context

POLICY_FIELDS=('name','start_time','end_time','last_sync_of_checkin',
               'determine_check_in_and_check_out','working_hours_calculation_based_on',
               'begin_check_in_before_shift_start_time','allow_check_out_after_shift_end_time')


def load_week(doc,employee,assignments,*,for_update=False):
    assignments=[frappe._dict(row) for row in assignments]
    end=get_datetime(doc.authorization_end)
    day=get_datetime(doc.authorization_start).date()
    first=day-timedelta(days=day.weekday())
    start=datetime.combine(first,time.min)
    rows=_reconciliation_rows('Employee Checkin',for_update=for_update,
        filters=[['employee','=',doc.employee],['time','>=',start-timedelta(days=1)],['time','<=',end]],
        fields=['name','time','log_type','shift','shift_start','shift_end','shift_actual_start','shift_actual_end',
                'skip_auto_attendance','offshift'],order_by='time asc, name asc',limit=4001)
    if len(rows)>4000:raise ValueError('La semana supera el límite de marcaciones; requiere revisión.')
    attendances=_reconciliation_rows('Attendance',for_update=for_update,
        filters={'employee':doc.employee,'docstatus':1,'attendance_date':['between',[first-timedelta(days=1),end.date()]]},
        fields=['name','attendance_date','status','docstatus','shift'],order_by='attendance_date asc, name asc',limit=101)
    if len(attendances)>100:raise ValueError('La semana supera el límite de asistencias; requiere revisión.')
    shifts={};policies={};schedules=[];issues=[]
    def shift(name):
        if name not in shifts:
            shifts[name]=frappe.get_doc('Shift Type',name,for_update=for_update)
            policies[name]={k:shifts[name].get(k) for k in POLICY_FIELDS}
            if shifts[name].get('custom_hora_salida_viernes'):
                policies[name]['custom_hora_salida_viernes']=shifts[name].get('custom_hora_salida_viernes')
        return shifts[name]
    for row in rows:
        if row.get('shift'):shift(row.shift)
    company=frappe.get_doc('Company',employee.company,for_update=for_update)
    day=first-timedelta(days=1)
    while day<=end.date():
        names={a.shift_type for a in assignments if getdate(a.start_date)<=day and (not a.end_date or getdate(a.end_date)>=day)}
        if not names and employee.get('default_shift'):names={employee.default_shift}
        if len(names)!=1:
            issues.append({'code':'weekly_shift_ambiguous' if names else 'weekly_shift_missing','date':str(day)})
        for name in sorted(names):
            current=shift(name)
            holidays=current.get('holiday_list') or employee.get('holiday_list') or company.get('default_holiday_list')
            context=get_schedule_context(day,name,holidays,for_update=for_update)
            context.update(date=str(day),shift=name)
            schedules.append(context)
        day+=timedelta(days=1)
    historical_intervals=[];historical_checkins=[];certified_sessions=[]
    previous=[]
    for source_type,mode_filter in [('Overtime Authorization',['evidence_enrolled','=',1]),
                                  ('Retroactive Overtime Adjustment',['reconciliation_engine','=','Verified Checkins'])]:
        filters=[['employee','=',doc.employee],['docstatus','in',[1,2]],mode_filter,
                 ['authorization_end','>',start-timedelta(days=1)],['authorization_end','<=',doc.authorization_start]]
        if source_type==doc.doctype:filters.append(['name','!=',doc.name])
        records=_reconciliation_rows(source_type,for_update=for_update,filters=filters,
            fields=['name','docstatus','authorization_start','reconciliation_source','evidence_snapshot'],order_by='authorization_start asc, name asc',limit=51)
        # Cancelling payment does not erase the physical work evidence.
        for record in records:
            if record.docstatus==2 and not record.evidence_snapshot:continue
            record['source_type']=source_type;previous.append(record)
    if len(previous)>50:raise ValueError('Demasiadas fuentes semanales; requiere revisión.')
    previous.sort(key=lambda row:(get_datetime(row.authorization_start),row.source_type,row.name))
    from powerpro.controllers.checkin_overtime import _data,_evidence_hash,now_datetime
    from powerpro.payroll_rules.overtime_evidence import evaluate_evidence
    for prior in previous:
        prior_doc=frappe.get_doc(prior.source_type,prior.name,for_update=for_update)
        if get_datetime(prior_doc.authorization_end)<=start:
            # A reviewed Sunday overrun can enter Monday even when the original
            # authorization ended Sunday. The bounded extra day finds it without
            # making unrelated previous-week sessions required evidence.
            from powerpro.controllers.overtime_history import effective_snapshot
            snapshot,_revision=effective_snapshot(prior_doc,for_update=for_update)
            window=(snapshot.get('input') or {}).get('observation_window')
            ends=[get_datetime(r['end']) for r in snapshot.get('worked_intervals',[])]
            if window:ends.append(get_datetime(window['end']))
            if not ends or max(ends)<=start:continue
        if prior.docstatus==2:
            from powerpro.controllers.overtime_history import compare
            history=compare(prior_doc,for_update=for_update)
            if not history['matches']:
                issues.append({'code':'weekly_previous_snapshot_changed','authorization':prior.name,'source_type':prior.source_type});continue
            fresh=history['current']
            certified_sessions.extend(fresh.get('certified_sessions',[]))
            historical_intervals.extend(fresh['worked_intervals'])
            historical_checkins.extend(name for session in fresh['sessions'] for name in session['checkins'])
            continue
        saved=frappe.parse_json(prior.evidence_snapshot or '{}')
        declaration=(saved.get('review') or {}).get('manual_declaration')
        if prior.reconciliation_source!='Employee Checkin' and not (prior.reconciliation_source=='Manual Verification' and declaration):
            issues.append({'code':'weekly_previous_verification_requires_review','authorization':prior.name,'source_type':prior.source_type});continue
        current,_settings=_data(frappe.get_doc(prior.source_type,prior.name,for_update=for_update),for_update=for_update,include_weekly=False)
        fresh=evaluate_evidence(authorization=current['authorization'],rows=current['rows'],shift=current['shift'],contexts=current['contexts'],
            next_windows=current['next_windows'],now=now_datetime(),competing=current['competing'])
        if declaration:
            from powerpro.payroll_rules.overtime_manual_session import evaluate_manual_session
            fresh=evaluate_manual_session(declaration=declaration,authorization=current['authorization'],rows=current['rows'],
                contexts=current['contexts'],now=now_datetime(),competing=current['competing'])
        acceptable=fresh['state']=='Verified' or (saved.get('review') and all(i['code']=='worked_authorized_mismatch' or i['severity']=='information' for i in fresh['issues']))
        if not acceptable or not saved.get('worked_intervals') or (
            _evidence_hash(saved.get('source_checkins'))!=_evidence_hash(fresh.get('source_checkins')) or
            _evidence_hash(saved['worked_intervals'])!=_evidence_hash(fresh.get('worked_intervals'))):
            issues.append({'code':'weekly_previous_snapshot_changed','authorization':prior.name,'source_type':prior.source_type});continue
        if declaration and (_evidence_hash(saved['input']['shift'])!=_evidence_hash(current['shift']) or _evidence_hash(saved['input']['contexts'])!=_evidence_hash(current['contexts'])):
            issues.append({'code':'weekly_previous_manual_context_changed','authorization':prior.name,'source_type':prior.source_type});continue
        certified_sessions.extend(fresh.get('certified_sessions',[]))
        historical_intervals.extend(fresh['worked_intervals'])
        historical_checkins.extend(name for session in fresh['sessions'] for name in session['checkins'])
    return {'start':start,'cutoff':end,'rows':[dict(r) for r in rows],
            'policies':policies,'schedules':schedules,'attendances':[dict(r) for r in attendances],
            'context_issues':issues,'certified_sessions':certified_sessions,'historical_intervals':historical_intervals,'historical_checkins':historical_checkins}
