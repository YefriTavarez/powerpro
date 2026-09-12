"""Persist evidence-based overtime, explicitly enrolled and independent of presumed attendance.

Lock order: Work Call -> Employee -> Authorization. Each worker unit is one caller-
owned transaction. No synthetic Checkins; audit runs are immutable.
"""
import hashlib
import json
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
from powerpro.payroll_rules.manual_overtime import verification_roles

AUTH='Overtime Authorization'
CALL='Overtime Work Call'
FINAL={'Created','Paid','Credited','Cancelled'}
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
    call.db_set('evidence_reconciliation_enabled',1)
    call.add_comment('Info',_('Conciliación por Employee Checkin inscrita; no se presume asistencia.'))


@frappe.whitelist(methods=['POST'])
def enroll(authorization):
    original=frappe.get_doc(AUTH,authorization);_access(original)
    doc,call=_lock(authorization)
    if call:frappe.throw(_('Seleccione Verified Checkins antes de enviar la convocatoria vinculada.'))
    enroll_authorization(doc)
    return {'authorization':doc.name,'status':doc.evidence_status}


def _data(doc,*,for_update=False):
    start,end=get_datetime(doc.authorization_start),get_datetime(doc.authorization_end)
    begin=datetime.combine(start.date(),time.min)-timedelta(days=1)
    finish=datetime.combine(end.date()+timedelta(days=1),time.min)
    rows=_reconciliation_rows('Employee Checkin',for_update=for_update,filters=[['employee','=',doc.employee],['time','>=',begin],['time','<',finish]],
        fields=['name','time','log_type','shift','shift_start','shift_end','shift_actual_start','shift_actual_end','skip_auto_attendance','offshift','modified'],order_by='time asc, name asc',limit=2001)
    if len(rows)>2000:raise ValueError('Demasiadas marcaciones en la ventana; requiere revisión.')
    shift=frappe.get_doc('Shift Type',doc.shift_type,for_update=for_update)
    days=list(calendar_dates(start,end));contexts=[]
    for day in [days[0]-timedelta(days=1)]+days:
        c=get_schedule_context(day,doc.shift_type,doc.holiday_list,for_update=for_update)
        c['date']=str(day);contexts.append(c)
    assignments=_reconciliation_rows('Shift Assignment',for_update=for_update,filters={'employee':doc.employee,'docstatus':1,'status':'Active','start_date':['<=',end.date()+timedelta(days=1)]},
        fields=['name','shift_type','start_date','end_date','modified'],limit=1001)
    if len(assignments)>1000:raise ValueError('Demasiadas asignaciones; requiere revisión.')
    employee=frappe.get_doc('Employee',doc.employee,for_update=for_update)
    next_windows=[]
    day=start.date()+timedelta(days=1)
    while day<=end.date():
        names={a.shift_type for a in assignments if getdate(a.start_date)<=day and (not a.end_date or getdate(a.end_date)>=day)}
        if not names and employee.get('default_shift'):names={employee.default_shift}
        for name in names:
            nxt=frappe.get_doc('Shift Type',name,for_update=for_update)
            a,b=get_shift_window(day,nxt.start_time,nxt.end_time)
            next_windows.append({'shift':name,'start':a-timedelta(minutes=flt(nxt.begin_check_in_before_shift_start_time)),
                'end':b+timedelta(minutes=flt(nxt.allow_check_out_after_shift_end_time))})
        day+=timedelta(days=1)
    competing=bool(_reconciliation_rows(AUTH,for_update=for_update,filters=[['employee','=',doc.employee],['docstatus','=',1],['name','!=',doc.name],['authorization_start','<',end],['authorization_end','>',start]],pluck='name',limit=1))
    settings=_settings()
    weekly=load_week(doc,employee,assignments,for_update=for_update)
    config={k:settings.get(k) for k in ['weekly_expected_hours','max_weekly_extra_hours','start_night_hours','end_night_hours','extra_hours_rate','extraordinary_hours_rate','night_hours_rate']}
    policy={k:shift.get(k) for k in ['name','modified','start_time','end_time','last_sync_of_checkin','determine_check_in_and_check_out','working_hours_calculation_based_on','begin_check_in_before_shift_start_time','allow_check_out_after_shift_end_time']}
    authorization={'name':doc.name,'start':str(start),'end':str(end),'shift':doc.shift_type,'maximum_hours':doc.maximum_hours}
    current_context=next(c for c in contexts if c['date']==str(start.date()))
    lower=min(start,get_datetime(current_context['shift_start']))-timedelta(minutes=flt(shift.begin_check_in_before_shift_start_time))
    upper=max(end,get_datetime(current_context['shift_end']))+timedelta(minutes=flt(shift.allow_check_out_after_shift_end_time))
    data={'calculator_version':VERSION,'authorization':authorization,'rows':[dict(r) for r in rows if lower<=get_datetime(r.time)<=upper],
          'shift':policy,'contexts':contexts,'next_windows':next_windows,'competing':competing,'weekly':weekly,'configuration':config,
          'assignments':[dict(r) for r in assignments if not r.end_date or getdate(r.end_date)>=getdate(weekly['start'])-timedelta(days=1)],
          'default_shift':employee.get('default_shift')}
    return data,settings


def build_result(doc,*,for_update=False):
    data,settings=_data(doc,for_update=for_update)
    result=evaluate_evidence(authorization=data['authorization'],rows=data['rows'],shift=data['shift'],contexts=data['contexts'],
        next_windows=data['next_windows'],now=now_datetime(),competing=data['competing'],
        night_start=coerce_time(settings.start_night_hours,time(21)),night_end=coerce_time(settings.end_night_hours,time(7)))
    if result.get('calculation'):
        accepted=[name for session in result['sessions'] for name in session['checkins']]
        weekly=collect_weekly_work(**data['weekly'],accepted_intervals=result['worked_intervals'],accepted_checkins=accepted)
        result['weekly_evidence']=weekly
        result['calculation']=apply_actual_week_bands(result['calculation'],weekly,threshold=settings.max_weekly_extra_hours)
        for field in ['regular_35_hours','regular_100_hours']:
            result['snapshot'][field]=result['calculation'][field]
    result['input_hash']=_evidence_hash(data)
    result['input']=data
    # Real-work validation is separate from pending weekly/premium policy approval.
    result['settlement_ready']=False
    result['settlement_blockers']=['La política de liquidación por evidencia debe estar validada antes de pagar.']
    if result.get('calculation') and not result['calculation']['weekly_evidence_complete']:
        result['settlement_blockers'].append('Falta evidencia semanal completa para clasificar el recargo de horas ordinarias extra.')
    return result


def _sync(call):
    if call:
        from powerpro.controllers.manual_overtime import _sync_work_call
        _sync_work_call(call)


def _audit(doc,result):
    run=frappe.new_doc('Overtime Reconciliation Run')
    run.update({'authorization':doc.name,'employee':doc.employee,'work_date':doc.work_date,'result_status':result['state'],
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
    if doc.get('reconciliation_source') in {'Manual Verification','HR Exception','Presumed Attendance'}:
        if doc.evidence_status!='Manual Verification':doc.db_set({'evidence_status':'Manual Verification','evidence_retry_after':None})
        return 'Manual Verification'
    result=build_result(doc,for_update=True)
    frozen=frappe.parse_json(doc.get('evidence_snapshot') or '{}')
    if frozen.get('input_hash') and frozen['input_hash']!=result['input_hash']:
        result['state']='Needs Review';result['issues'].append({'code':'verified_source_changed','severity':'review'})
        result.pop('snapshot',None)
    changed=doc.get('evidence_last_hash')!=result['input_hash'] or doc.get('evidence_status')!=result['state']
    if changed:_audit(doc,result)
    visible_issues=list(result['issues'])
    visible_issues.extend({**issue,'scope':'weekly_settlement'} for issue in result.get('weekly_evidence',{}).get('issues',[]))
    visible_issues.extend({'code':'settlement_pending','scope':'settlement','message':message} for message in result['settlement_blockers'])
    values={'evidence_status':result['state'],'evidence_last_hash':result['input_hash'],
        'evidence_last_attempt':now_datetime(),'evidence_retry_after':now_datetime()+timedelta(minutes=5 if result['state']=='Waiting' else 10),
        'evidence_issues':_json(visible_issues),'evidence_settlement_ready':0}
    if result.get('snapshot') and result['state']=='Verified' and (changed or not doc.get('reconciled_on')):
        values.update(result['snapshot'])
        values.update(reconciliation_source='Employee Checkin',presumed_hours=0,presumed_on=None,
            source_checkins=_json(result['source_checkins']),reconciliation_intervals=_json(result['calculation']['intervals']),
            unapproved_intervals=_json(result['calculation']['unapproved_intervals']),reconciliation_warnings=_json(result['issues']),
            reconciled_by=frappe.session.user,reconciled_on=now_datetime(),evidence_snapshot=_json(result))
    elif not doc.get('reconciled_on'):
        values['reconciliation_status']='Scheduled' if result['state']=='Waiting' else 'Check-in Issue'
    doc.db_set(values)
    _sync(call)
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
    return result


def validate_settlement(doc,*,for_update=False):
    if not doc.get('evidence_enrolled'):return
    if doc.get('evidence_status') not in {'Verified','Manual Verification'} or not doc.get('evidence_settlement_ready'):
        frappe.throw(_('Complete la revisión de evidencia y de su política antes de liquidar.'))
    if not cint(_settings().get('enable_checkin_overtime_reconciliation')):
        frappe.throw(_('La liquidación del modo por marcaciones está pausada.'))
    if doc.get('reconciliation_source')!='Employee Checkin':
        frappe.throw(_('La verificación manual requiere una revisión de liquidación independiente.'))
    frozen=frappe.parse_json(doc.get('evidence_snapshot') or '{}')
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
