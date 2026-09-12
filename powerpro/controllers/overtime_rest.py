"""Employee election, approved leave linkage and evidenced rest enjoyment."""
import hashlib,json
from contextlib import contextmanager
from datetime import timedelta
import frappe
from frappe import _
from frappe.utils import cint,flt,get_datetime,getdate,now_datetime
from powerpro.controllers.overtime import _reconciliation_rows,get_schedule_context
from powerpro.controllers.overtime_pay_policy import get_effective_policy
from powerpro.payroll_rules.overtime_rest import rest_entitlement,validate_rest_schedule

from powerpro.controllers.overtime_source import AUTH,RETRO,evidence_enabled,identity,get_source,claim

DT='Overtime Settlement Election'


@contextmanager
def managed(action,name):
    old=frappe.flags.get('overtime_election_action')
    frappe.flags.overtime_election_action=(action,name)
    try:yield
    finally:frappe.flags.overtime_election_action=old


def require_managed(action,name):
    if frappe.flags.get('overtime_election_action')!=(action,name):
        frappe.throw(_('Utilice las acciones de elección y descanso.'),frappe.PermissionError)


def _lock_source(name,*,allow_cancelled=False,source_type=AUTH):
    if source_type==RETRO:
        ref=frappe.db.get_value(RETRO,name,'employee')
        if not ref:frappe.throw(_('El ajuste retroactivo no existe.'))
        frappe.db.get_value('Employee',ref,'name',for_update=True)
        doc=frappe.get_doc(RETRO,name,for_update=True)
        if doc.employee!=ref:frappe.throw(_('El empleado del ajuste cambió; vuelva a intentar.'))
        from powerpro.controllers.checkin_overtime import _access
        _access(doc)
        if not evidence_enabled(doc):frappe.throw(_('El ajuste requiere conciliación por marcaciones.'))
        if not allow_cancelled and (doc.docstatus!=1 or doc.status!='Approved'):
            frappe.throw(_('El ajuste debe permanecer aprobado.'))
        return doc,None
    if source_type!=AUTH:frappe.throw(_('Origen de horas extra no admitido.'))
    from powerpro.controllers.checkin_overtime import _lock,_access
    if not allow_cancelled:
        auth,call=_lock(name)
    else:
        ref=frappe.db.get_value('Overtime Authorization',name,['employee','overtime_work_call'],as_dict=True)
        if not ref:frappe.throw(_('La autorización no existe.'))
        call=frappe.get_doc('Overtime Work Call',ref.overtime_work_call,for_update=True) if ref.overtime_work_call else None
        frappe.db.get_value('Employee',ref.employee,'name',for_update=True)
        auth=frappe.get_doc('Overtime Authorization',name,for_update=True)
    _access(auth)
    return auth,call


def _locked_election(name,*,allow_cancelled=False):
    ref=frappe.get_doc(DT,name);ref.check_permission('write')
    source_type,source_name=identity(ref)
    auth,call=_lock_source(source_name,allow_cancelled=allow_cancelled,source_type=source_type)
    election=frappe.get_doc(DT,name,for_update=True);election.check_permission('write')
    if identity(election)!=(auth.doctype,auth.name):
        frappe.throw(_('La autorización de la elección cambió; vuelva a intentar.'))
    return election,auth,call


def get_election(auth,*,for_update=False):
    rows=_reconciliation_rows(DT,for_update=for_update,
        filters={'active_authorization':claim(auth),'docstatus':1},fields=['name'],limit=2)
    if not rows:return None
    if len(rows)!=1:frappe.throw(_('Hay elecciones activas duplicadas.'))
    return frappe.get_doc(DT,rows[0].name,for_update=for_update)


def _weekly(auth,calculation=None):
    from powerpro.payroll_rules.overtime_combined_day import combined_hours
    if calculation is None:calculation=frappe.parse_json(auth.get('evidence_snapshot') or '{}').get('calculation')
    return bool(flt((calculation or {}).get('weekly_rest_hours',auth.get('weekly_rest_hours')))
        or combined_hours(calculation) or auth.get('day_classification') in {'Weekly Rest','Legal Holiday on Weekly Rest'})


def election_snapshot(election):
    if not election:return None
    fields=['retroactive_adjustment','settlement_payroll_date'] if election.get('retroactive_adjustment') else (['settlement_payroll_date'] if election.get('settlement_payroll_date') else [])
    return json.loads(json.dumps({k:election.get(k) for k in fields+['name','authorization','employee','choice','employee_reference','policy',
        'planned_start','planned_end','minimum_rest_hours','credit_hours','required_leave_days','weekly_rest',
        'approved_by','approved_on']},default=str))


def validate_election(election,auth,policy,*,worked_hours=None,calculation=None):
    if not evidence_enabled(auth) or auth.docstatus!=1 or auth.status!='Approved':
        frappe.throw(_('La autorización debe estar aprobada e inscrita por marcaciones.'))
    if identity(election)!=(auth.doctype,auth.name):frappe.throw(_('La elección no corresponde al origen.'))
    if not str(election.employee_reference or '').strip():frappe.throw(_('Adjunte o referencie la elección expresa del empleado.'))
    if election.choice not in {'Cash','Compensatory Rest'}:frappe.throw(_('Seleccione efectivo o descanso.'))
    if not policy or (election.policy and election.policy!=policy['name']):frappe.throw(_('La política aprobada no coincide con esta elección.'))
    weekly=_weekly(auth,calculation)
    values={'employee':auth.employee,'company':auth.company,'policy':policy['name'],'weekly_rest':int(weekly)}
    if election.choice=='Cash':
        if auth.doctype==RETRO:
            from powerpro.payroll_rules.retroactive_overtime import is_settlement_payroll_date_valid
            date=election.get('settlement_payroll_date') or auth.get('settlement_payroll_date')
            if not date or not is_settlement_payroll_date_valid(auth.work_date,date):
                frappe.throw(_('Indique una fecha de nómina igual o posterior al trabajo para la elección de pago.'))
            values['settlement_payroll_date']=getdate(date)
        if weekly and not policy.get('weekly_rest_cash'):frappe.throw(_('La política no autoriza efectivo por descanso semanal.'))
        values.update(credit_hours=0,minimum_rest_hours=0,required_leave_days=0)
    else:
        from powerpro.payroll_rules.overtime_combined_day import combined_hours
        actual_calculation=calculation if calculation is not None else frappe.parse_json(auth.get('evidence_snapshot') or '{}').get('calculation')
        if combined_hours(actual_calculation):
            from powerpro.payroll_rules.overtime_combined_day import hybrid_cash_calculation
            hybrid_cash_calculation(policy,actual_calculation)
            from powerpro.payroll_rules.retroactive_overtime import is_settlement_payroll_date_valid
            date=election.get('settlement_payroll_date')
            if not date or not is_settlement_payroll_date_valid(auth.work_date,date):
                frappe.throw(_('Indique fecha de nómina para pagar el feriado junto con el descanso.'))
            values['settlement_payroll_date']=getdate(date)
        total=worked_hours if worked_hours is not None else (auth.verified_hours or auth.maximum_hours)
        weekly_hours=flt((calculation or {}).get('weekly_rest_hours',auth.get('weekly_rest_hours')))
        if weekly and weekly_hours and abs(flt(total)-weekly_hours)>.0001:
            frappe.throw(_('La autorización mezcla descanso semanal y otras horas; revise sus obligaciones separadas antes de acreditar descanso.'))
        entitlement=rest_entitlement(policy,total,weekly_rest=weekly)
        validate_rest_schedule(election.planned_start,election.planned_end,work_date=auth.work_date,
                               authorization_end=auth.authorization_end,entitlement=entitlement)
        values.update(entitlement)
    if election.docstatus==1 and any(abs(flt(election.get(k))-flt(values[k]))>.0001 for k in ['weekly_rest','credit_hours','minimum_rest_hours','required_leave_days']):
        frappe.throw(_('La elección ya no coincide con la obligación calculada; requiere revisión.'))
    return values


def _event(auth,election,action,details):
    from powerpro.controllers.checkin_overtime import _audit
    payload={'election':election.name,'action':action,'details':details,'actor':frappe.session.user}
    _audit(auth,{'state':action,'input_hash':hashlib.sha256(json.dumps(payload,sort_keys=True,default=str).encode()).hexdigest(),
                 'issues':[],'rest_event':payload})


@frappe.whitelist(methods=['POST'])
def approve_election(name):
    election,auth,_call=_locked_election(name)
    if election.docstatus!=0:frappe.throw(_('La elección ya fue procesada.'))
    from powerpro.controllers import checkin_overtime as evidence
    saved=frappe.parse_json(auth.evidence_snapshot or '{}')
    certified=bool(auth.reconciliation_source=='Manual Verification' and (saved.get('review') or {}).get('manual_declaration'))
    if auth.evidence_status!='Verified' or flt(auth.verified_hours)<=0 or (auth.reconciliation_source!='Employee Checkin' and not certified):
        frappe.throw(_('Concilie primero las marcaciones o la jornada declarada para elegir sobre horas verificadas.'))
    if certified and not cint(evidence._settings().get('enable_manual_overtime_verification')):
        frappe.throw(_('La verificación manual está desactivada.'))
    current=evidence.build_result(auth,for_update=True)
    if (current['state']!='Verified' or not saved.get('input_hash') or saved['input_hash']!=current['input_hash']
            or evidence._evidence_hash(saved.get('snapshot'))!=evidence._evidence_hash(current.get('snapshot'))):
        frappe.throw(_('La evidencia cambió. Revise las horas antes de aprobar la elección del empleado.'))
    if auth.settlement_status in {'Created','Payroll Submitted','Paid','Credited','Cancelled'}:frappe.throw(_('No se cambia la elección de una obligación ya liquidada.'))
    with managed('submit',name):
        election.flags.ignore_permissions=True;election.submit()
    values={'planned_settlement':election.choice,'evidence_settlement_ready':0}
    if auth.doctype==AUTH:values['evidence_retry_after']=now_datetime()
    elif election.choice=='Cash':values['settlement_payroll_date']=election.settlement_payroll_date
    if election.get('settlement_payroll_date'):values['settlement_payroll_date']=election.settlement_payroll_date
    auth.db_set(values)
    _event(auth,election,'Employee Election Approved',election_snapshot(election))
    return {'name':name,'status':election.status}


def release_for_source(auth):
    """Called inside source cancellation; outer transaction also reverses its funds."""
    election=get_election(auth,for_update=True)
    if not election:return
    with managed('cancel',election.name):
        election.flags.ignore_permissions=True;election.cancel()
    _event(auth,election,'Election Cancelled With Source',{})


@frappe.whitelist(methods=['POST'])
def cancel_election(name,reason):
    if not str(reason or '').strip():frappe.throw(_('Indique el motivo.'))
    election,auth,_call=_locked_election(name,allow_cancelled=True)
    if auth.settlement_status in {'Created','Payroll Submitted','Paid','Credited'}:frappe.throw(_('Revierta primero la liquidación vinculada.'))
    with managed('cancel',name):
        election.flags.ignore_permissions=True;election.cancel()
    values={'evidence_settlement_ready':0}
    if auth.doctype==AUTH:values['evidence_retry_after']=now_datetime()
    auth.db_set(values)
    _event(auth,election,'Employee Election Cancelled',{'reason':reason})
    return {'status':'Cancelled'}


def _check_leave_coverage(auth,election,leave,*,start=None,end=None,for_update=False):
    start=get_datetime(start or election.planned_start);end=get_datetime(end or election.planned_end)
    policy=frappe.parse_json(auth.evidence_snapshot)['input']['pay_policy']
    if leave.docstatus!=1 or leave.status!='Approved' or leave.employee!=auth.employee or leave.leave_type!=policy['leave_type']:
        frappe.throw(_('La licencia debe estar enviada, aprobada y corresponder al empleado y tipo de descanso.'))
    employee=frappe.get_doc('Employee',auth.employee,for_update=for_update)
    company=frappe.get_doc('Company',auth.company,for_update=for_update)
    assignments=_reconciliation_rows('Shift Assignment',for_update=for_update,filters={'employee':auth.employee,'docstatus':1,'status':'Active','start_date':['<=',end.date()]},
        fields=['shift_type','start_date','end_date'],limit=1001)
    if len(assignments)>1000:frappe.throw(_('Demasiados turnos; revise la programación.'))
    required=[];day=start.date()-timedelta(days=1)
    while day<=end.date():
        names={r.shift_type for r in assignments if getdate(r.start_date)<=day and (not r.end_date or getdate(r.end_date)>=day)}
        if not names and employee.default_shift:names={employee.default_shift}
        if len(names)!=1:frappe.throw(_('Se requiere un turno inequívoco para comprobar la cobertura del descanso.'))
        shift=frappe.get_doc('Shift Type',next(iter(names)),for_update=for_update)
        context=get_schedule_context(day,shift.name,shift.get('holiday_list') or employee.get('holiday_list') or company.get('default_holiday_list'),for_update=for_update)
        if not context['holiday_list_covers_work_date']:frappe.throw(_('El calendario no cubre el descanso.'))
        if context['classification']=='Regular Workday' and get_datetime(context['shift_start'])<end and get_datetime(context['shift_end'])>start:
            if leave.half_day and getdate(leave.half_day_date)==day:
                shift_start,shift_end=get_datetime(context['shift_start']),get_datetime(context['shift_end'])
                overlap=(min(end,shift_end)-max(start,shift_start)).total_seconds()
                if overlap>(shift_end-shift_start).total_seconds()/2+.001:
                    frappe.throw(_('Una licencia de medio día no cubre la jornada completa afectada por el descanso.'))
            required.append(day)
        day+=timedelta(days=1)
    if not required:frappe.throw(_('El descanso no libera ninguna jornada programada; requiere revisión.'))
    if any(not getdate(leave.from_date)<=day<=getdate(leave.to_date) for day in required):
        frappe.throw(_('La licencia no cubre todas las jornadas que coinciden con el descanso.'))
    claims=_reconciliation_rows(DT,for_update=for_update,filters={'leave_application':leave.name,'docstatus':1,'name':['!=',election.name]},fields=['required_leave_days'])
    if flt(election.required_leave_days)+sum(flt(r.required_leave_days) for r in claims)>flt(leave.total_leave_days)+.0001:
        frappe.throw(_('La licencia no cubre los días reclamados por estas obligaciones de descanso.'))
    return required


@frappe.whitelist(methods=['POST'])
def link_leave(name,leave_application):
    election,auth,_call=_locked_election(name)
    if election.docstatus!=1 or election.choice!='Compensatory Rest' or election.status=='Enjoyed' or auth.settlement_status!='Credited':
        frappe.throw(_('Se requiere un crédito de descanso vigente y pendiente de disfrute.'))
    if frappe.db.get_value('Overtime Compensatory Credit',auth.compensatory_credit,'docstatus',for_update=True)!=1:
        frappe.throw(_('El crédito de descanso no está vigente.'))
    leave=frappe.get_doc('Leave Application',leave_application,for_update=True);leave.check_permission('read')
    _check_leave_coverage(auth,election,leave,for_update=True)
    election.db_set({'leave_application':leave.name,'status':'Scheduled'})
    _event(auth,election,'Rest Scheduled',{'leave_application':leave.name})
    return {'status':'Scheduled'}


@frappe.whitelist(methods=['POST'])
def confirm_enjoyment(name,actual_start,actual_end,reference):
    if not str(reference or '').strip():frappe.throw(_('Referencie la verificación del descanso con el empleado.'))
    election,auth,_call=_locked_election(name)
    if election.status=='Enjoyed':
        if get_datetime(election.actual_start)!=get_datetime(actual_start) or get_datetime(election.actual_end)!=get_datetime(actual_end) or election.enjoyment_reference!=reference:
            frappe.throw(_('El disfrute ya está confirmado; utilice la acción de corrección para cambiarlo.'))
        return {'status':'Enjoyed'}
    if election.docstatus!=1 or auth.settlement_status!='Credited' or not election.leave_application:
        frappe.throw(_('Vincule primero una licencia aprobada al crédito de descanso.'))
    if frappe.db.get_value('Overtime Compensatory Credit',auth.compensatory_credit,'docstatus',for_update=True)!=1:
        frappe.throw(_('El crédito de descanso no está vigente.'))
    a,b=get_datetime(actual_start),get_datetime(actual_end)
    validate_rest_schedule(a,b,work_date=auth.work_date,authorization_end=auth.authorization_end,
        entitlement={'minimum_rest_hours':election.minimum_rest_hours,'weekly_rest':election.weekly_rest})
    if b>now_datetime():frappe.throw(_('No se confirma un descanso que aún no terminó.'))
    leave=frappe.get_doc('Leave Application',election.leave_application,for_update=True)
    _check_leave_coverage(auth,election,leave,start=a,end=b,for_update=True)
    if _reconciliation_rows('Employee Checkin',for_update=True,filters=[['employee','=',auth.employee],['time','>=',a],['time','<',b]],pluck='name',limit=1):
        frappe.throw(_('Hay marcaciones durante el descanso declarado; resuelva la discrepancia antes de confirmarlo.'))
    if _reconciliation_rows(DT,for_update=True,filters=[['employee','=',auth.employee],['docstatus','=',1],['status','=','Enjoyed'],
        ['name','!=',name],['actual_start','<',b],['actual_end','>',a]],pluck='name',limit=1):
        frappe.throw(_('Ese intervalo de descanso ya cumple otra obligación.'))
    election.db_set({'status':'Enjoyed','actual_start':a,'actual_end':b,'enjoyment_reference':reference,
                     'confirmed_by':frappe.session.user,'confirmed_on':now_datetime()})
    _event(auth,election,'Rest Enjoyment Confirmed',{'start':str(a),'end':str(b),'reference':reference,'leave_application':leave.name})
    return {'status':'Enjoyed'}


def before_leave_cancel(leave,method=None):
    rows=_reconciliation_rows(DT,for_update=True,filters={'leave_application':leave.name,'docstatus':1},fields=['name','status','authorization','retroactive_adjustment'])
    if any(r.status=='Enjoyed' for r in rows):frappe.throw(_('Revise primero la confirmación de disfrute vinculada a esta licencia.'))
    for row in rows:
        election=frappe.get_doc(DT,row.name,for_update=True)
        election.db_set({'leave_application':None,'status':'Credited'})
        _event(get_source(row),election,'Linked Leave Cancelled',{'leave_application':leave.name})


@frappe.whitelist(methods=['POST'])
def revoke_enjoyment(name,reason):
    if not str(reason or '').strip():frappe.throw(_('Documente por qué se corrige la confirmación de disfrute.'))
    election,auth,_call=_locked_election(name)
    if election.status!='Enjoyed':frappe.throw(_('No hay una confirmación de disfrute vigente.'))
    _event(auth,election,'Rest Enjoyment Revoked',{'reason':reason,'previous':{k:election.get(k) for k in ['actual_start','actual_end','enjoyment_reference','confirmed_by','confirmed_on']}})
    election.db_set({'status':'Scheduled','actual_start':None,'actual_end':None,'enjoyment_reference':None,'confirmed_by':None,'confirmed_on':None})
    return {'status':'Scheduled'}


@frappe.whitelist(methods=['POST'])
def reschedule(name,start,end,reason):
    if not str(reason or '').strip():frappe.throw(_('Documente el motivo de la reprogramación.'))
    election,auth,_call=_locked_election(name)
    if election.docstatus!=1 or election.choice!='Compensatory Rest' or election.status=='Enjoyed':
        frappe.throw(_('La elección no admite reprogramación en su estado actual.'))
    if election.leave_application:frappe.throw(_('Cancele primero la licencia anterior para evitar consumir el saldo dos veces.'))
    prior={'start':election.planned_start,'end':election.planned_end}
    election.planned_start=start;election.planned_end=end
    frozen=frappe.parse_json(auth.evidence_snapshot or '{}')
    policy=frozen.get('input',{}).get('pay_policy') or get_effective_policy(auth)
    validate_election(election,auth,policy)
    others=_reconciliation_rows(DT,for_update=True,filters=[['employee','=',auth.employee],['docstatus','=',1],
        ['active_authorization','is','set'],['choice','=','Compensatory Rest'],['name','!=',name],['planned_start','<',end],['planned_end','>',start]],pluck='name',limit=1)
    if others:frappe.throw(_('La nueva ventana se superpone con otro descanso.'))
    election.db_set({'planned_start':start,'planned_end':end,'status':'Credited' if auth.settlement_status=='Credited' else 'Approved'})
    _event(auth,election,'Rest Rescheduled',{'previous':prior,'start':start,'end':end,'reason':reason})
    return {'status':election.status}


@frappe.whitelist()
def get_rest_status(name):
    """Current operational proof; never infer enjoyment from absence of punches."""
    election=frappe.get_doc(DT,name);election.check_permission('read')
    auth=get_source(election);auth.check_permission('read')
    frappe.get_doc('Employee',auth.employee).check_permission('read')
    from powerpro.controllers.checkin_overtime import _evidence_hash
    from powerpro.controllers.overtime_source import identity
    refs=[{'document_type':DT,'document_name':election.name},
          {'document_type':auth.doctype,'document_name':auth.name}]
    proof={'election':{k:election.get(k) for k in ['name','docstatus','status','active_authorization','employee','company','choice',
        'planned_start','planned_end','actual_start','actual_end','confirmed_by','confirmed_on','enjoyment_reference','leave_application']},
        'source':{'doctype':auth.doctype,'name':auth.name,'docstatus':auth.docstatus,'status':auth.status,
            'settlement_status':auth.settlement_status,'compensatory_credit':auth.get('compensatory_credit'),'leave_allocation':auth.get('leave_allocation')}}
    issues=[]
    def issue(code):issues.append({'code':code})
    def finish(status):
        return {'status':status,'settlement_status':auth.settlement_status,'leave_application':election.leave_application,
            'credit':auth.get('compensatory_credit'),'allocation':auth.get('leave_allocation'),'issues':issues,
            'evidence':proof,'evidence_hash':_evidence_hash({'proof':proof,'issues':issues,'status':status}),'references':refs}
    if election.docstatus==2 or auth.docstatus==2:return finish('Cancelled')
    if election.docstatus!=1:return finish('Draft')
    if election.choice!='Compensatory Rest':return finish('Not Applicable')
    if (auth.docstatus!=1 or auth.status!='Approved' or not evidence_enabled(auth)
            or auth.planned_settlement!=election.choice or election.active_authorization!=claim(auth) or election.employee!=auth.employee or election.company!=auth.company):
        issue('inactive_or_mismatched_election');return finish('Review')
    if not election.planned_start or not election.planned_end:
        issue('missing_rest_window');return finish('Review')
    try:
        validate_rest_schedule(election.planned_start,election.planned_end,work_date=auth.work_date,
            authorization_end=auth.authorization_end,entitlement={'minimum_rest_hours':election.minimum_rest_hours,'weekly_rest':election.weekly_rest})
    except ValueError:
        issue('invalid_rest_window');return finish('Review')
    # A changing work record calls for review; it never silently reduces an
    # already created rest obligation or changes the frozen source.
    from powerpro.controllers import checkin_overtime as evidence
    from powerpro.controllers.overtime_history import physical_input
    saved=frappe.parse_json(auth.evidence_snapshot or '{}')
    current=evidence.build_result(auth)
    checkins={r['name'] for r in (current.get('source_checkins') or [])+(saved.get('source_checkins') or [])}
    if not frappe.has_permission('Employee Checkin','read'):
        frappe.throw(_('Necesita acceso a las marcaciones para verificar el descanso.'),frappe.PermissionError)
    for checkin in sorted(checkins):
        if not frappe.has_permission('Employee Checkin','read',doc=checkin):
            frappe.throw(_('No tiene acceso a una marcación necesaria para verificar el descanso.'),frappe.PermissionError)
        refs.append({'document_type':'Employee Checkin','document_name':checkin})
    proof['physical_work']={'saved_hash':_evidence_hash(physical_input(saved)),
        'current_hash':_evidence_hash(physical_input(current)),'current_state':current['state']}
    if proof['physical_work']['saved_hash']!=proof['physical_work']['current_hash'] or current['state']!='Verified':
        issue('work_evidence_changed')
    credited=auth.settlement_status=='Credited'
    if credited:
        if not auth.get('compensatory_credit'):
            issue('missing_compensatory_credit')
        else:
            credit=frappe.get_doc('Overtime Compensatory Credit',auth.compensatory_credit);credit.check_permission('read')
            refs.append({'document_type':credit.doctype,'document_name':credit.name})
            proof['credit']={k:credit.get(k) for k in ['name','docstatus','status','employee','banked_hours','credited_days','leave_allocation']}
            if credit.docstatus!=1 or credit.status!='Credited' or credit.employee!=auth.employee or identity(credit,authorization_field='overtime_authorization')!=(auth.doctype,auth.name):
                issue('inactive_or_mismatched_credit')
            if credit.leave_allocation and credit.leave_allocation!=auth.get('leave_allocation'):
                issue('credit_allocation_link_changed')
    elif auth.settlement_status in {'Created','Payroll Submitted','Paid','Cancelled'}:
        issue('settlement_inconsistent_with_rest')
    if auth.get('leave_allocation'):
        allocation=frappe.get_doc('Leave Allocation',auth.leave_allocation);allocation.check_permission('read')
        refs.append({'document_type':allocation.doctype,'document_name':allocation.name})
        proof['allocation']={k:allocation.get(k) for k in ['name','docstatus','employee','leave_type','from_date','to_date']}
        policy=saved.get('input',{}).get('pay_policy') or {}
        if allocation.docstatus!=1 or allocation.employee!=auth.employee or allocation.leave_type!=policy.get('leave_type'):
            issue('inactive_or_mismatched_allocation')
    leave=None
    if election.leave_application:
        leave=frappe.get_doc('Leave Application',election.leave_application);leave.check_permission('read')
        refs.append({'document_type':leave.doctype,'document_name':leave.name})
        proof['leave']={k:leave.get(k) for k in ['name','docstatus','status','employee','leave_type','from_date','to_date','half_day','half_day_date','total_leave_days']}
        try:
            if election.status=='Enjoyed':
                _check_leave_coverage(auth,election,leave,start=election.actual_start,end=election.actual_end)
            else:_check_leave_coverage(auth,election,leave)
        except frappe.ValidationError:issue('leave_no_longer_covers_rest')
    if election.status=='Enjoyed':
        if (not credited or not leave or not election.actual_start or not election.actual_end
                or not election.enjoyment_reference or not election.confirmed_by or not election.confirmed_on):
            issue('incomplete_enjoyment_confirmation')
        else:
            a,b=get_datetime(election.actual_start),get_datetime(election.actual_end)
            try:validate_rest_schedule(a,b,work_date=auth.work_date,authorization_end=auth.authorization_end,
                entitlement={'minimum_rest_hours':election.minimum_rest_hours,'weekly_rest':election.weekly_rest})
            except ValueError:issue('invalid_confirmed_rest_window')
            if b>now_datetime():issue('confirmed_rest_has_not_ended')
            conflicts=frappe.get_all('Employee Checkin',filters=[['employee','=',auth.employee],['time','>=',a],['time','<',b]],fields=['name','time'],limit=101)
            if len(conflicts)>100:frappe.throw(_('Demasiadas marcaciones en el descanso; acote la revisión.'))
            for row in conflicts:
                if not frappe.has_permission('Employee Checkin','read',doc=row.name):
                    frappe.throw(_('No tiene acceso a una marcación del descanso.'),frappe.PermissionError)
                refs.append({'document_type':'Employee Checkin','document_name':row.name})
            proof['rest_checkins']=conflicts
            if conflicts:issue('checkin_during_confirmed_rest')
        return finish('Review' if issues else 'Enjoyed')
    if election.status=='Scheduled' and (not credited or not leave):issue('missing_scheduled_rest_support')
    if issues:return finish('Review')
    if get_datetime(election.planned_end)<now_datetime():return finish('Overdue')
    return finish('Scheduled' if leave else 'Credited' if credited else 'Approved')
