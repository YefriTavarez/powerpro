"""Persist evidence-based overtime, explicitly enrolled and independent of presumed attendance.

Lock order: Work Call -> Employee -> Authorization. Each worker unit is one caller-
owned transaction. No synthetic Checkins; audit runs are immutable.
"""
import hashlib
import json
from math import isfinite
from datetime import datetime,time,timedelta
import frappe
from frappe import _
from frappe.utils import cint,flt,get_datetime,getdate,now_datetime
from powerpro.controllers.overtime import get_schedule_context,_reconciliation_rows
from powerpro.payroll_rules.overtime import coerce_time,get_shift_window
from powerpro.payroll_rules.overtime_calendar import calendar_dates
from powerpro.payroll_rules.overtime_evidence import VERSION,evaluate_evidence
from powerpro.payroll_rules.overtime_actual_week import collect_weekly_work,apply_actual_week_bands
from powerpro.controllers.checkin_overtime_week import load_week
from powerpro.controllers.overtime_pay_policy import get_effective_policy
from powerpro.payroll_rules.overtime_pay_policy import classify_night_session
from powerpro.payroll_rules.manual_overtime import verification_roles

AUTH='Overtime Authorization'
CALL='Overtime Work Call'
FINAL={'Created','Payroll Submitted','Paid','Credited','Cancelled'}
FIELDS=('evidence_enrolled','evidence_status','evidence_enrolled_by','evidence_enrolled_on','evidence_last_hash',
        'evidence_last_attempt','evidence_retry_after','evidence_issues','evidence_snapshot','evidence_settlement_ready','evidence_auto_settle')


def _json(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,default=str)
def _settings():return frappe.get_single('DGII Payroll Settings')


def _evidence_hash(data):
    # Advancing the synchronization watermark does not change worked time.
    # Regressed/incomplete synchronization still prevents verification via state.
    def semantic(value):
        if isinstance(value,dict):
            return {k:semantic(v) for k,v in value.items() if k not in {'modified','last_sync_of_checkin'}}
        if isinstance(value,(list,tuple)):return [semantic(v) for v in value]
        return value
    return hashlib.sha256(_json(semantic(data)).encode()).hexdigest()


def validate_enrollment(doc,settings=None):
    settings=settings or _settings()
    if not cint(settings.get('enable_checkin_overtime_reconciliation')):
        frappe.throw(_('La conciliación automática con marcaciones está desactivada.'))
    effective=settings.get('checkin_overtime_effective_from')
    start=doc.get('from_date') if doc.doctype==CALL else doc.work_date
    if not effective or getdate(start)<getdate(effective):
        frappe.throw(_('La fecha de trabajo debe estar cubierta por la fecha efectiva de conciliación.'))
    if doc.get('automatic_settlement_enabled') or doc.get('auto_enrolled'):
        frappe.throw(_('La asistencia presumida existente requiere una transición explícita; no se convierte automáticamente.'))


def _access(doc):
    doc.check_permission('read');doc.check_permission('write')
    if not verification_roles(_settings().get('overtime_manual_verification_roles')).intersection(frappe.get_roles(frappe.session.user)):
        frappe.throw(_('Su rol no permite administrar la conciliación de marcaciones.'),frappe.PermissionError)


def _lock(name):
    ref=frappe.db.get_value(AUTH,name,['employee','overtime_work_call'],as_dict=True)
    if not ref:frappe.throw(_('La autorización no existe.'))
    call=frappe.get_doc(CALL,ref.overtime_work_call,for_update=True) if ref.overtime_work_call else None
    frappe.db.get_value('Employee',ref.employee,'name',for_update=True)
    doc=frappe.get_doc(AUTH,name,for_update=True)
    if doc.employee!=ref.employee or doc.overtime_work_call!=ref.overtime_work_call:frappe.throw(_('La autorización cambió; vuelva a intentar.'))
    if doc.docstatus!=1 or doc.status!='Approved' or (call and call.docstatus!=1):frappe.throw(_('La autorización y su convocatoria deben permanecer enviadas.'))
    return doc,call


def enroll_authorization(doc,*,auto_settle=False):
    validate_enrollment(doc)
    if doc.get('evidence_enrolled'):return
    if doc.get('reconciled_on') or doc.get('settlement_status') in FINAL:
        frappe.throw(_('Solo se inscriben autorizaciones nuevas sin conciliación ni liquidación.'))
    doc.db_set({'evidence_enrolled':1,'evidence_status':'Pending','evidence_enrolled_by':frappe.session.user,
        'evidence_enrolled_on':now_datetime(),'evidence_retry_after':now_datetime(),'evidence_auto_settle':cint(auto_settle)})


def enroll_call(call):
    validate_enrollment(call)
    if call.docstatus!=1:frappe.throw(_('Envíe la convocatoria antes de inscribirla.'))
    names=frappe.get_all(AUTH,filters={'overtime_work_call':call.name,'docstatus':1},pluck='name')
    if len(names)!=cint(call.authorization_count):frappe.throw(_('El conjunto de autorizaciones está incompleto.'))
    for name in names:
        doc,_call=_lock(name)
        enroll_authorization(doc,auto_settle=call.get('evidence_auto_settle'))
        if call.get('evidence_auto_settle'):
            from powerpro.controllers.automatic_overtime import _payroll_date
            doc.db_set('auto_payroll_date',_payroll_date(call,doc.work_date,_settings().get('overtime_auto_payroll_date_policy') or 'Work Date'))
    call.db_set('evidence_reconciliation_enabled',1)
    call.add_comment('Info',_('Conciliación por Employee Checkin inscrita; no se presume asistencia.'))


@frappe.whitelist(methods=['POST'])
def enroll(authorization):
    original=frappe.get_doc(AUTH,authorization);_access(original)
    doc,call=_lock(authorization)
    if call:frappe.throw(_('Seleccione Verified Checkins antes de enviar la convocatoria vinculada.'))
    enroll_authorization(doc)
    return {'authorization':doc.name,'status':doc.evidence_status}


def _data(doc,*,for_update=False,include_weekly=True,observation_window=None):
    start,end=get_datetime(doc.authorization_start),get_datetime(doc.authorization_end)
    observed_start,observed_end=start,end
    if observation_window is not None:
        if doc.docstatus!=2:raise ValueError('La ventana histórica solo se admite en orígenes cancelados.')
        from powerpro.payroll_rules.overtime_observation_window import normalize_window
        base=get_schedule_context(start.date(),doc.shift_type,doc.holiday_list,for_update=for_update)
        observation_window=normalize_window(observation_window,min(start,get_datetime(base['shift_start'])),max(end,get_datetime(base['shift_end'])))
        observed_start,observed_end=get_datetime(observation_window['start']),get_datetime(observation_window['end'])
    begin=datetime.combine(observed_start.date(),time.min)-timedelta(days=1)
    finish=datetime.combine(observed_end.date()+timedelta(days=1),time.min)
    rows=_reconciliation_rows('Employee Checkin',for_update=for_update,filters=[['employee','=',doc.employee],['time','>=',begin],['time','<',finish]],
        fields=['name','time','log_type','shift','shift_start','shift_end','shift_actual_start','shift_actual_end','skip_auto_attendance','offshift','modified'],order_by='time asc, name asc',limit=2001)
    if len(rows)>2000:raise ValueError('Demasiadas marcaciones en la ventana; requiere revisión.')
    shift=frappe.get_doc('Shift Type',doc.shift_type,for_update=for_update)
    days=list(calendar_dates(observed_start,observed_end));contexts=[]
    for day in [days[0]-timedelta(days=1)]+days:
        c=get_schedule_context(day,doc.shift_type,doc.holiday_list,for_update=for_update)
        c['date']=str(day);contexts.append(c)
    assignments=_reconciliation_rows('Shift Assignment',for_update=for_update,filters={'employee':doc.employee,'docstatus':1,'status':'Active','start_date':['<=',observed_end.date()+timedelta(days=1)]},
        fields=['name','shift_type','start_date','end_date','modified'],limit=1001)
    if len(assignments)>1000:raise ValueError('Demasiadas asignaciones; requiere revisión.')
    employee=frappe.get_doc('Employee',doc.employee,for_update=for_update)
    next_windows=[]
    day=observed_start.date()-timedelta(days=1) if observation_window else start.date()+timedelta(days=1)
    while day<=observed_end.date():
        if day==start.date():
            day+=timedelta(days=1);continue
        names={a.shift_type for a in assignments if getdate(a.start_date)<=day and (not a.end_date or getdate(a.end_date)>=day)}
        if not names and employee.get('default_shift'):names={employee.default_shift}
        for name in names:
            nxt=frappe.get_doc('Shift Type',name,for_update=for_update)
            a,b=get_shift_window(day,nxt.start_time,nxt.end_time)
            next_windows.append({'shift':name,'start':a-timedelta(minutes=flt(nxt.begin_check_in_before_shift_start_time)),
                'end':b+timedelta(minutes=flt(nxt.allow_check_out_after_shift_end_time)),
                **({'relation':'previous'} if day<start.date() else {})})
        day+=timedelta(days=1)
    competing=False
    for source_type in [AUTH,'Retroactive Overtime Adjustment']:
        filters=[['employee','=',doc.employee],['docstatus','=',1],['authorization_start','<',end],['authorization_end','>',start]]
        if source_type==doc.doctype:filters.append(['name','!=',doc.name])
        if _reconciliation_rows(source_type,for_update=for_update,filters=filters,pluck='name',limit=1):competing=True
    settings=_settings()
    pay_policy=get_effective_policy(doc,for_update=for_update)
    salary_fields=['name','base','from_date']
    if frappe.get_meta('Salary Structure Assignment').has_field('salary_per_hour'):salary_fields.append('salary_per_hour')
    assignments_for_pay=_reconciliation_rows('Salary Structure Assignment',for_update=for_update,
        filters={'employee':doc.employee,'company':doc.company,'docstatus':1,'from_date':['<=',doc.work_date]},
        fields=salary_fields,order_by='from_date desc, creation desc',limit=1)
    rate_basis=None
    if assignments_for_pay and (flt(assignments_for_pay[0].get('salary_per_hour'))>0 or flt(assignments_for_pay[0].base)>0):
        from powerpro.controllers.overtime_cash_settlement import _get_hourly_rate
        rate_basis={**dict(assignments_for_pay[0]),'hourly_rate':_get_hourly_rate(assignments_for_pay[0])}
        if not isfinite(rate_basis['hourly_rate']) or rate_basis['hourly_rate']<=0:rate_basis=None
    week_start=datetime.combine(start.date()-timedelta(days=start.weekday()),time.min)
    weekly=load_week(doc,employee,assignments,for_update=for_update) if include_weekly else {'start':week_start}
    config={k:settings.get(k) for k in ['weekly_expected_hours','max_weekly_extra_hours','start_night_hours','end_night_hours','extra_hours_rate','extraordinary_hours_rate','night_hours_rate']}
    policy={k:shift.get(k) for k in ['name','modified','start_time','end_time','last_sync_of_checkin','determine_check_in_and_check_out','working_hours_calculation_based_on','begin_check_in_before_shift_start_time','allow_check_out_after_shift_end_time']}
    authorization={'name':doc.name,'start':str(start),'end':str(end),'shift':doc.shift_type,'maximum_hours':flt(doc.maximum_hours)}
    current_context=next(c for c in contexts if c['date']==str(start.date()))
    lower=min(start,get_datetime(current_context['shift_start']))-timedelta(minutes=flt(shift.begin_check_in_before_shift_start_time))
    upper=max(end,get_datetime(current_context['shift_end']))+timedelta(minutes=flt(shift.allow_check_out_after_shift_end_time))
    if observation_window is not None:
        lower=observed_start-timedelta(minutes=flt(shift.begin_check_in_before_shift_start_time))
        upper=observed_end+timedelta(minutes=flt(shift.allow_check_out_after_shift_end_time))
    data={'calculator_version':VERSION,'pay_policy':pay_policy,'rate_basis':rate_basis,'authorization':authorization,'rows':[dict(r) for r in rows if lower<=get_datetime(r.time)<=upper],
          'shift':policy,'contexts':contexts,'next_windows':next_windows,'competing':competing,'weekly':weekly,'configuration':config,
          'assignments':[dict(r) for r in assignments if not r.end_date or getdate(r.end_date)>=getdate(weekly['start'])-timedelta(days=1)],
          'default_shift':employee.get('default_shift')}
    if observation_window is not None:data['observation_window']=observation_window
    from powerpro.controllers.overtime_holiday_base import latest
    coverage=latest(doc,for_update=for_update)
    if coverage:data['holiday_base_coverage']=coverage
    return data,settings


def build_result(doc,*,for_update=False,use_saved_review=True,manual_declaration=None):
    data,settings=_data(doc,for_update=for_update)
    policy=data['pay_policy']
    saved=frappe.parse_json(doc.get('evidence_snapshot') or '{}')
    if manual_declaration is None and use_saved_review:
        manual_declaration=(saved.get('review') or {}).get('manual_declaration')
    result=evaluate_evidence(authorization=data['authorization'],rows=data['rows'],shift=data['shift'],contexts=data['contexts'],
        next_windows=data['next_windows'],now=now_datetime(),competing=data['competing'],
        night_start=time(21) if policy else coerce_time(settings.start_night_hours,time(21)),
        night_end=time(7) if policy else coerce_time(settings.end_night_hours,time(7)))
    if manual_declaration is not None:
        from powerpro.payroll_rules.overtime_manual_session import evaluate_manual_session
        comparison=result
        result=evaluate_manual_session(declaration=manual_declaration,authorization=data['authorization'],rows=data['rows'],
            contexts=data['contexts'],now=now_datetime(),competing=data['competing'],night_start=time(21),night_end=time(7))
        result['checkin_comparison']=comparison
        data['manual_declaration']=manual_declaration
    blockers=[]
    if not policy:blockers.append('Falta una política de liquidación aprobada que cubra la fecha de trabajo.')
    if doc.planned_settlement=='Cash' and not data['rate_basis']:
        blockers.append('Falta una asignación salarial vigente con tarifa por hora válida.')
    if result.get('calculation'):
        accepted=[name for session in result['sessions'] for name in session['checkins']]
        weekly_data=dict(data['weekly'])
        historical_intervals=weekly_data.pop('historical_intervals',[])
        historical_checkins=weekly_data.pop('historical_checkins',[])
        certified_sessions=weekly_data.pop('certified_sessions',[])
        weekly=collect_weekly_work(**weekly_data,accepted_intervals=historical_intervals+result['worked_intervals'],accepted_checkins=historical_checkins+accepted,certified_sessions=certified_sessions+result.get('certified_sessions',[]))
        result['weekly_evidence']=weekly
        result['calculation']=apply_actual_week_bands(result['calculation'],weekly,threshold=policy['weekly_threshold'] if policy else settings.max_weekly_extra_hours)
        for field in ['regular_35_hours','regular_100_hours']:
            result['snapshot'][field]=result['calculation'][field]
        if policy:
            night=classify_night_session(result['worked_intervals'],result['calculation']['intervals'],basis=policy['night_basis'])
            result['night_session']=night
            result['snapshot']['night_hours']=result['calculation']['night_hours']=night['overtime_premium_hours']
            if policy['night_basis']=='Whole nocturnal session' and night['classification']=='Nocturna':
                for segment in result['calculation']['segments']:segment['night_hours']=segment['verified_hours']
            if night['ordinary_premium_hours']:
                from powerpro.controllers.ordinary_night import coverage_for_authorization,COVERAGE_PENDING
                coverage=coverage_for_authorization(doc,result,for_update=for_update)
                result['ordinary_night_settlement']=coverage
                if not coverage:
                    blockers.append(COVERAGE_PENDING)
        from powerpro.payroll_rules.overtime_combined_day import settlement_blocker
        combined_blocker=settlement_blocker(policy,result['calculation'],doc.planned_settlement)
        if combined_blocker:blockers.append(combined_blocker)
    result['input_hash']=_evidence_hash(data)
    result['input']=data
    result['settlement_blockers']=blockers
    from powerpro.payroll_rules.overtime_combined_day import combined_hours,REST_FIELD
    hybrid=bool(doc.planned_settlement=='Compensatory Rest' and combined_hours(result.get('calculation')) and (policy or {}).get(REST_FIELD))
    if hybrid and not data['rate_basis']:blockers.append('Falta la tarifa salarial para el pago del feriado.')
    if policy and (doc.planned_settlement=='Cash' or hybrid):
        from powerpro.controllers.overtime_holiday_base import apply_to_result
        apply_to_result(result)
    if result.get('calculation') and not result['calculation']['weekly_evidence_complete']:
        blockers.append('Falta evidencia semanal completa para clasificar el recargo de horas ordinarias extra.')
    from powerpro.controllers.overtime_rest import get_election,validate_election,election_snapshot
    election=get_election(doc,for_update=for_update)
    from powerpro.payroll_rules.overtime_combined_day import combined_hours
    needs_election=doc.planned_settlement=='Compensatory Rest' or bool(result.get('calculation',{}).get('weekly_rest_hours')) or bool(combined_hours(result.get('calculation')))
    result['settlement_election']=election_snapshot(election)
    if needs_election and not election:
        blockers.append('Falta la elección expresa del empleado y la programación del descanso cuando corresponda.')
    if election:
        try:
            validate_election(election,doc,policy,worked_hours=result.get('snapshot',{}).get('verified_hours'),calculation=result.get('calculation'))
            if election.choice!=doc.planned_settlement:blockers.append('La elección del empleado no coincide con la forma de liquidación.')
        except (ValueError,frappe.ValidationError) as exc:blockers.append(str(exc))
    result['settlement_ready']=bool(result['state']=='Verified' and result.get('snapshot') and not blockers)
    result['settlement_blockers']=blockers
    if use_saved_review:
        saved=frappe.parse_json(doc.get('evidence_snapshot') or '{}')
        if saved.get('review'):
            from powerpro.controllers.checkin_overtime_review import accept_result
            result=accept_result(result,saved['review'])
    return result


def _sync(call):
    if call:
        from powerpro.controllers.manual_overtime import _sync_work_call
        _sync_work_call(call)


def _audit(doc,result):
    from powerpro.controllers.overtime_source import links
    run=frappe.new_doc('Overtime Reconciliation Run')
    run.update({**links(doc),'employee':doc.employee,'work_date':doc.work_date,'result_status':result['state'],
        'evidence_hash':result['input_hash'],'evidence':_json(result),'issues':_json(result['issues']),
        'evaluated_by':frappe.session.user,'evaluated_on':now_datetime()})
    run.name=frappe.generate_hash(length=16);run.db_insert()


def process_authorization(name):
    if not cint(_settings().get('enable_checkin_overtime_reconciliation')):return 'Paused'
    doc,call=_lock(name)
    if not doc.get('evidence_enrolled'):return 'Not Enrolled'
    if doc.get('settlement_status') in FINAL:
        if doc.evidence_status!='Frozen':doc.db_set('evidence_status','Frozen')
        return 'Frozen'
    frozen=frappe.parse_json(doc.get('evidence_snapshot') or '{}')
    certified_manual=bool(doc.get('reconciliation_source')=='Manual Verification' and (frozen.get('review') or {}).get('manual_declaration'))
    if doc.get('reconciliation_source') in {'Manual Verification','HR Exception','Presumed Attendance'} and not certified_manual:
        if doc.evidence_status!='Manual Verification':doc.db_set({'evidence_status':'Manual Verification','evidence_retry_after':None})
        return 'Manual Verification'
    if certified_manual and not cint(_settings().get('enable_manual_overtime_verification')):
        return 'Manual Verification'
    result=build_result(doc,for_update=True)
    if frozen.get('input_hash') and frozen['input_hash']!=result['input_hash']:
        result['state']='Needs Review';result['issues'].append({'code':'verified_source_changed','severity':'review'})
        result['settlement_ready']=False
        result.pop('snapshot',None)
    changed=(doc.get('evidence_last_hash')!=result['input_hash'] or doc.get('evidence_status')!=result['state']
             or cint(doc.get('evidence_settlement_ready'))!=cint(result['settlement_ready']))
    if changed:_audit(doc,result)
    visible_issues=list(result['issues'])
    visible_issues.extend({**issue,'scope':'weekly_settlement'} for issue in result.get('weekly_evidence',{}).get('issues',[]))
    visible_issues.extend({'code':'settlement_pending','scope':'settlement','message':message} for message in result['settlement_blockers'])
    values={'evidence_status':result['state'],'evidence_last_hash':result['input_hash'],
        'evidence_last_attempt':now_datetime(),'evidence_retry_after':now_datetime()+timedelta(minutes=5 if result['state']=='Waiting' else 10),
        'evidence_issues':_json(visible_issues),'evidence_settlement_ready':cint(result['settlement_ready'])}
    if certified_manual and result['state']=='Verified':
        # Coverage/election readiness can change; the HR-certified work and actor cannot.
        if _evidence_hash(result.get('snapshot'))!=_evidence_hash(frozen.get('snapshot')):
            frappe.throw(_('El cálculo de la jornada declarada cambió; requiere revisión de Gestión Humana.'))
        values['evidence_snapshot']=_json(result)
    elif result.get('snapshot') and result['state']=='Verified' and (changed or not doc.get('reconciled_on')):
        values.update(result['snapshot'])
        values.update(reconciliation_source='Employee Checkin',presumed_hours=0,presumed_on=None,
            source_checkins=_json(result['source_checkins']),reconciliation_intervals=_json(result['calculation']['intervals']),
            unapproved_intervals=_json(result['calculation']['unapproved_intervals']),reconciliation_warnings=_json(result['issues']),
            reconciled_by=frappe.session.user,reconciled_on=now_datetime(),evidence_snapshot=_json(result))
    elif not doc.get('reconciled_on'):
        values['reconciliation_status']='Scheduled' if result['state']=='Waiting' else 'Check-in Issue'
    doc.db_set(values)
    _sync(call)
    from powerpro.controllers.ordinary_night import automatic_coverage_allowed,create_automatic_coverage
    auto_night=automatic_coverage_allowed(doc,result)
    if doc.get('evidence_auto_settle') and (result['settlement_ready'] or auto_night):
        frappe.db.savepoint('checkin_cash_settlement')
        try:
            if auto_night:
                create_automatic_coverage(doc,result)
                ready=build_result(doc,for_update=True)
                if (not ready['settlement_ready'] or ready['input_hash']!=result['input_hash']
                        or _evidence_hash(ready.get('snapshot'))!=_evidence_hash(result.get('snapshot'))):
                    frappe.throw(_('La evidencia cambió al completar la cobertura nocturna.'))
                doc.db_set({'evidence_snapshot':_json(ready),'evidence_settlement_ready':1,'evidence_issues':_json(ready['issues'])})
                _audit(doc,ready)
            from powerpro.controllers.overtime_settlement import _settle_authorization
            _settle_authorization(doc,payroll_date=doc.auto_payroll_date,settings=_settings())
            doc.db_set({'evidence_status':'Frozen','evidence_retry_after':None})
            return 'Frozen'
        except Exception as exc:
            frappe.db.rollback(save_point='checkin_cash_settlement')
            doc.reload()
            doc.db_set('evidence_issues',_json(visible_issues+[{'code':'settlement_error','scope':'settlement','message':str(exc)[:1500]}]))
    return result['state']


@frappe.whitelist(methods=['POST'])
def process_now(authorization):
    doc=frappe.get_doc(AUTH,authorization);_access(doc)
    status=process_authorization(doc.name)
    return {'authorization':doc.name,'status':status}


@frappe.whitelist()
def get_status(authorization):
    doc=frappe.get_doc(AUTH,authorization);doc.check_permission('read')
    result={k:doc.get(k) for k in FIELDS}
    result['can_process']=bool(frappe.has_permission(AUTH,'write',doc=doc) and verification_roles(_settings().get('overtime_manual_verification_roles')).intersection(frappe.get_roles(frappe.session.user)))
    result['enabled']=bool(cint(_settings().get('enable_checkin_overtime_reconciliation')))
    result['manual_review_allowed']=bool(cint(_settings().get('enable_manual_overtime_verification')))
    from powerpro.controllers.overtime_rest import get_election
    election=get_election(doc)
    result['election']=election.name if election else None
    result['can_night']=frappe.has_permission('Ordinary Night Settlement','create')
    if result['can_night']:
        result['ordinary_night']=frappe.db.get_value('Ordinary Night Settlement',
            {'employee':doc.employee,'work_date':doc.work_date,'docstatus':1},'name')
    return result


def validate_settlement(doc,*,for_update=False,payroll=False):
    if not doc.get('evidence_enrolled'):return
    allowed={'Verified','Manual Verification'} | ({'Frozen'} if payroll else set())
    if doc.get('evidence_status') not in allowed or not doc.get('evidence_settlement_ready'):
        frappe.throw(_('Complete la revisión de evidencia y de su política antes de liquidar.'))
    if not payroll and not cint(_settings().get('enable_checkin_overtime_reconciliation')):
        frappe.throw(_('La liquidación del modo por marcaciones está pausada.'))
    frozen=frappe.parse_json(doc.get('evidence_snapshot') or '{}')
    manual=(frozen.get('review') or {}).get('manual_declaration')
    if manual and not payroll and not cint(_settings().get('enable_manual_overtime_verification')):
        frappe.throw(_('La liquidación de evidencia manual está desactivada.'))
    if doc.get('reconciliation_source')!='Employee Checkin' and not (doc.reconciliation_source=='Manual Verification' and manual):
        frappe.throw(_('La verificación manual requiere una revisión de liquidación independiente.'))
    current=build_result(doc,for_update=for_update)
    if not frozen.get('input_hash') or frozen['input_hash']!=current['input_hash'] or current['state']!='Verified':
        frappe.throw(_('La evidencia cambió o está incompleta; concilie y revise antes de liquidar.'))
    if not current.get('settlement_ready') or not current.get('calculation',{}).get('weekly_evidence_complete'):
        frappe.throw(_('La evidencia semanal y la política vigente deben habilitar esta liquidación.'))
    snapshot=frozen.get('snapshot') or {}
    for field in ['verified_hours','regular_35_hours','regular_100_hours','holiday_100_hours','weekly_rest_hours','night_hours']:
        if field not in snapshot or abs(flt(doc.get(field))-flt(snapshot[field]))>.00005:
            frappe.throw(_('Las horas del documento no coinciden con su evidencia guardada.'))
    for field in ['actual_start','actual_end']:
        if not snapshot.get(field) or not doc.get(field) or get_datetime(doc.get(field))!=get_datetime(snapshot[field]):
            frappe.throw(_('El horario real no coincide con su evidencia guardada.'))


def scheduled_reconcile_due():
    if not cint(_settings().get('enable_checkin_overtime_reconciliation')):return
    names=frappe.get_all(AUTH,filters={'evidence_enrolled':1,'docstatus':1,'evidence_status':['in',['Pending','Waiting','Needs Review','Verified']],
        'evidence_retry_after':['<=',now_datetime()]},pluck='name',order_by='authorization_start asc, name asc',limit=100)
    for name in names:
        try:process_authorization(name);frappe.db.commit()
        except Exception as exc:
            frappe.db.rollback()
            try:
                doc,_call=_lock(name)
                doc.db_set({'evidence_status':'Needs Review','evidence_settlement_ready':0,
                    'evidence_issues':_json([{'code':'processing_error','message':str(exc)[:1500]}]),'evidence_retry_after':now_datetime()+timedelta(minutes=10)})
                frappe.db.commit()
            except Exception:frappe.db.rollback()
