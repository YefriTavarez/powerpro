"""Monitor approved compensatory-rest elections without changing their ledger."""
from contextlib import contextmanager
from datetime import timedelta
import frappe
from frappe import _
from frappe.utils import cint,get_datetime,now_datetime
from powerpro.controllers import overtime_rest as rest,overtime_evidence_monitor as base
from powerpro.controllers.overtime_source import identity
from powerpro.controllers.checkin_overtime import _evidence_hash,_json
from powerpro.payroll_rules.manual_overtime import verification_roles

DT='Overtime Rest Watch'
SETTINGS='DGII Payroll Settings'
REFERENCE_TYPES=(rest.DT,'Overtime Authorization','Retroactive Overtime Adjustment','Overtime Compensatory Credit','Leave Allocation','Leave Application','Employee Checkin')
LABELS={'Approved':'Pendiente de crédito','Credited':'Pendiente de programar licencia','Scheduled':'Descanso programado',
    'Enjoyed':'Disfrute respaldado','Overdue':'Descanso previsto vencido: verificar disfrute','Review':'Requiere revisión de evidencia y respaldo',
    'Cancelled':'Elección u origen cancelado','Draft':'Elección en borrador','Not Applicable':'La elección no corresponde a descanso',
    'Access Required':'Revise el responsable y su acceso','Error':'Falló la comprobación; revise el registro de errores'}


def enabled():return bool(cint(frappe.db.get_single_value(SETTINGS,'enable_overtime_rest_monitor')))


def watch_permission(doc,ptype=None,user=None,**kwargs):
    return (base.watch_permission(doc,ptype,user) and frappe.has_permission(rest.DT,'read',doc=doc.election,user=user)
        and frappe.has_permission('Employee','read',doc=doc.employee,user=user)
        and all(r.document_type in REFERENCE_TYPES and frappe.has_permission(r.document_type,'read',doc=r.document_name,user=user)
            for r in (doc.get('evidence_references') or [])))


def watch_query(user=None):
    from frappe.model.db_query import DatabaseQuery
    user=user or frappe.session.user
    source=base.source_query(DT,user)
    if user=='Administrator':return source
    refs='`tabWorking Time Evidence Reference`';allowed=[]
    for dt in REFERENCE_TYPES:
        if not frappe.has_permission(dt,'read',user=user):continue
        query=DatabaseQuery(dt,user=user);query.fields=['name'];query.tables=['`tab'+dt+'`']
        condition=query.build_match_conditions()
        allowed.append('('+refs+'.document_type='+frappe.db.escape(dt)
            +' AND EXISTS(SELECT 1 FROM `tab'+dt+'` WHERE `tab'+dt+'`.name='+refs+'.document_name'
            +(' AND ('+condition+')' if condition else '')+'))')
    permitted=' OR '.join(allowed) or '1=0'
    return ('('+(source or '1=1')+') AND NOT EXISTS(SELECT 1 FROM '+refs+' WHERE '+refs+'.parent=`tabOvertime Rest Watch`.name'
        +" AND "+refs+".parenttype='Overtime Rest Watch' AND "+refs+".parentfield='evidence_references' AND NOT ("+permitted+'))')


@contextmanager
def _writing():
    old=frappe.flags.get('overtime_rest_watch_write');frappe.flags.overtime_rest_watch_write=True
    try:yield
    finally:frappe.flags.overtime_rest_watch_write=old


def _responsible(election,source,user):
    if not user or not frappe.db.get_value('User',user,'enabled'):
        frappe.throw(_('Seleccione un responsable activo para el descanso.'),frappe.PermissionError)
    if not verification_roles(base.evidence._settings().get('overtime_manual_verification_roles')).intersection(frappe.get_roles(user)):
        frappe.throw(_('El responsable necesita un rol configurado para revisar evidencia.'),frappe.PermissionError)
    for dt,name in [(DT,None),(rest.DT,election.name),(source.doctype,source.name),('Employee',source.employee)]:
        if not frappe.has_permission(dt,'read',doc=name,user=user):
            frappe.throw(_('El responsable necesita acceso a la elección, origen, empleado y seguimiento.'),frappe.PermissionError)


def _watch(election,source):
    name=frappe.db.get_value(DT,{'election':election.name},'name',for_update=True)
    if name:return frappe.get_doc(DT,name,for_update=True)
    return frappe.get_doc(dict(doctype=DT,election=election.name,source_type=source.doctype,source_name=source.name,
        employee=source.employee,company=source.company,responsible=election.approved_by,
        evidence_references=[{'document_type':rest.DT,'document_name':election.name},{'document_type':source.doctype,'document_name':source.name}]))


def _locked(election_name):
    ref=frappe.get_doc(rest.DT,election_name);ref.check_permission('read')
    dt,name=identity(ref)
    source,_=rest._lock_source(name,allow_cancelled=True,source_type=dt)
    election=frappe.get_doc(rest.DT,election_name,for_update=True);election.check_permission('read')
    if identity(election)!=(source.doctype,source.name):frappe.throw(_('El origen de la elección cambió.'))
    watch=_watch(election,source)
    if (watch.source_type,watch.source_name,watch.employee)!=(source.doctype,source.name,source.employee):
        frappe.throw(_('El origen del seguimiento cambió; requiere revisión.'))
    return election,source,watch


def _update(watch,values):
    changed=watch.is_new() or any(str(watch.get(k) or '')!=str(v or '') for k,v in values.items() if k!='evidence_references')
    watch.checked_on=now_datetime()
    if changed:
        watch.update(values);watch.changed_on=watch.checked_on
        with _writing():watch.save(ignore_permissions=True)
    else:watch.db_set('checked_on',watch.checked_on,update_modified=False)


def _notice(watch):
    if not cint(frappe.db.get_single_value(SETTINGS,'enable_overtime_rest_notices')):return {'notice_status':'Disabled'}
    if watch.status not in {'Approved','Credited','Overdue','Review'}:
        return {'notice_status':'No action pending','last_notice_key':None}
    from frappe.desk.doctype.notification_settings.notification_settings import is_notifications_enabled
    if not is_notifications_enabled(watch.responsible):return {'notice_status':'User muted'}
    key=_evidence_hash({'election':watch.election,'evidence':watch.evidence_hash,'responsible':watch.responsible,'status':watch.status})
    days=cint(frappe.db.get_single_value(SETTINGS,'overtime_rest_reminder_days'))
    due=bool(0<days<=30 and watch.last_notice_on and get_datetime(watch.last_notice_on)+timedelta(days=days)<=now_datetime())
    if watch.last_notice_key==key and not due:return {'notice_status':'Unchanged'}
    subjects={'Approved':'Hay un descanso compensatorio pendiente de acreditar.','Credited':'Hay un descanso compensatorio pendiente de programar.',
        'Overdue':'Un descanso compensatorio previsto venció; verifique su disfrute.','Review':'Un descanso compensatorio requiere revisar su evidencia y respaldo.'}
    notice=frappe.get_doc(dict(doctype='Notification Log',type='Alert',for_user=watch.responsible,from_user=frappe.session.user,
        subject=_(subjects[watch.status]),document_type=DT,document_name=watch.name))
    notice.insert(ignore_permissions=True)
    return {'notice_status':'Sent','last_notice_key':key,'last_notice_on':now_datetime(),'last_notice':notice.name}


def process_election(name):
    if not enabled():return {'status':'Disabled'}
    election,source,watch=_locked(name)
    original=frappe.session.user
    try:
        _responsible(election,source,watch.responsible);frappe.set_user(watch.responsible)
        if not watch.is_new():watch.check_permission('read')
        result=rest.get_rest_status(election.name)
        values={'status':result['status'],'summary':_(LABELS[result['status']]),'planned_start':election.planned_start,
            'planned_end':election.planned_end,'evidence_hash':result['evidence_hash'],'evidence':_json(result['evidence']),
            'issues':_json(result['issues']),'evidence_references':result['references']}
        _update(watch,values)
        # Both watch changes and the native Alert are one scheduler transaction.
        _update(watch,_notice(watch))
        return {'name':watch.name,'status':watch.status,'notice_status':watch.notice_status}
    finally:frappe.set_user(original)


def _record_failure(name,exc):
    election=frappe.get_doc(rest.DT,name);source=rest.get_source(election)
    watch=_watch(election,source)
    status='Access Required' if isinstance(exc,frappe.PermissionError) else 'Review' if isinstance(exc,(frappe.ValidationError,ValueError)) else 'Error'
    _update(watch,{'status':status,'summary':_(LABELS[status]),'notice_status':'Not sent'})


def _candidates(limit=30):
    election=frappe.qb.DocType(rest.DT);watch=frappe.qb.DocType(DT)
    return (frappe.qb.from_(election).left_join(watch).on(watch.election==election.name).select(election.name)
        .where(election.docstatus.isin([1,2])&(election.choice=='Compensatory Rest'))
        .where((election.docstatus==1)|watch.name.isnull()|(watch.status!='Cancelled'))
        .where(watch.name.isnull()|(watch.checked_on<now_datetime()-timedelta(hours=1)))
        .orderby(watch.checked_on).orderby(election.creation).orderby(election.name)
        .limit(max(1,min(cint(limit),100))).run(as_dict=True))


def scheduled_check():
    if not enabled():return
    for row in _candidates():
        try:process_election(row.name);frappe.db.commit()
        except Exception as exc:
            trace=frappe.get_traceback();frappe.db.rollback()
            try:_record_failure(row.name,exc);frappe.db.commit()
            except Exception:
                frappe.db.rollback();frappe.log_error(title='Overtime rest monitor',message=frappe.get_traceback())
            if not isinstance(exc,(frappe.ValidationError,frappe.PermissionError,ValueError)):
                frappe.log_error(title='Overtime rest monitor',message=trace)


@frappe.whitelist(methods=['POST'])
def recheck(name):
    watch=frappe.get_doc(DT,name);watch.check_permission('read')
    return process_election(watch.election)


@frappe.whitelist(methods=['POST'])
def assign(name,responsible,reason):
    watch=frappe.get_doc(DT,name);watch.check_permission('read')
    election,source,watch=_locked(watch.election)
    _responsible(election,source,responsible)
    if any(not frappe.has_permission(r.document_type,'read',doc=r.document_name,user=responsible) for r in watch.evidence_references):
        frappe.throw(_('El responsable necesita acceso a todos los documentos de respaldo.'),frappe.PermissionError)
    reason=str(reason or '').strip()
    if not reason:frappe.throw(_('Explique el motivo de la reasignación.'))
    if watch.responsible==responsible:return {'name':watch.name,'changed':False}
    _update(watch,{'responsible':responsible,'change_reason':reason,'last_notice_key':None})
    return {'name':watch.name,'changed':True}
