"""Explicit immutable evaluation enrollment; new cases use its chosen rules."""
from contextlib import contextmanager
from datetime import timedelta
import frappe
from frappe import _
from frappe.utils import cint,now_datetime
from powerpro.controllers import working_time_incidents as cases
from powerpro.controllers import working_time_incident_monitor as monitor
from powerpro.controllers.checkin_overtime import _evidence_hash,_json

DT='Working Time Review'


def review_query(user=None):
    return cases.monitor.source_query(DT,user)


def review_permission(doc,ptype=None,user=None,**kwargs):
    return (cases.monitor.watch_permission(doc,ptype,user) and bool(doc.employee)
        and frappe.has_permission('Employee','read',doc=doc.employee,user=user))


def _responsible(source,user):
    cases._responsible(source,user)
    if not frappe.has_permission(DT,'read',user=user):
        frappe.throw(_('El responsable necesita acceso a las evaluaciones vigiladas.'),frappe.PermissionError)


def ensure_review(source,options,responsible):
    if not frappe.has_permission(DT,'read'):frappe.throw(_('Necesita acceso a las evaluaciones vigiladas.'),frappe.PermissionError)
    _responsible(source,responsible)
    key=_evidence_hash(dict(source_type=source.doctype,source_name=source.name,options=options))
    name=frappe.db.get_value(DT,{'review_key':key},'name',for_update=True)
    if name:
        review=frappe.get_doc(DT,name,for_update=True);review.check_permission('read')
        if review.responsible!=responsible:
            frappe.throw(_('Esta evaluación ya tiene un responsable; use su acción de reasignación.'))
        return review
    review=frappe.get_doc(dict(doctype=DT,source_type=source.doctype,source_name=source.name,employee=source.employee,
        company=source.company,work_date=source.work_date,responsible=responsible,status='Active',evaluation_options=_json(options),
        registered_by=frappe.session.user,registered_on=now_datetime(),review_key=key,
        change_reason=_('Inscripción explícita de condiciones para detectar incidencias nuevas; no certifica su aplicabilidad legal.')))
    with cases._writing():review.insert(ignore_permissions=True)
    return review


def _locked(name):
    ref=frappe.get_doc(DT,name);ref.check_permission('read')
    source=cases.monitor._source(ref.source_type,ref.source_name);cases._access(source)
    review=frappe.get_doc(DT,name,for_update=True);review.check_permission('read')
    if (review.source_type,review.source_name,review.employee)!=(source.doctype,source.name,source.employee):
        frappe.throw(_('El origen de la evaluación cambió; requiere revisión.'))
    return review,source


@frappe.whitelist(methods=['POST'])
def configure(name,status,responsible,reason):
    review,source=_locked(name)
    if status not in {'Active','Paused'}:frappe.throw(_('Seleccione un estado válido.'))
    _responsible(source,responsible)
    reason=str(reason or '').strip()
    if not reason:frappe.throw(_('Explique el motivo del cambio.'))
    changed=review.status!=status or review.responsible!=responsible
    if changed:
        review.update(dict(status=status,responsible=responsible,change_reason=reason,monitor_checked_on=None))
        with cases._writing():review.save(ignore_permissions=True)
    return {'name':review.name,'status':review.status,'changed':changed}


def _save_state(review,status,message):
    values={'monitor_status':status,'monitor_message':message}
    if any(str(review.get(k) or '')!=str(v or '') for k,v in values.items()):
        review.update({**values,'monitor_checked_on':now_datetime()})
        with cases._writing():review.save(ignore_permissions=True)
    else:review.db_set('monitor_checked_on',now_datetime(),update_modified=False)


@contextmanager
def _as_responsible(review,source):
    original=frappe.session.user
    try:
        if not frappe.db.get_value('User',review.responsible,'enabled'):
            frappe.throw(_('El responsable de la evaluación está deshabilitado.'),frappe.PermissionError)
        _responsible(source,review.responsible);frappe.set_user(review.responsible)
        review.check_permission('read');cases._access(source)
        yield
    finally:frappe.set_user(original)


def process_review(name):
    if not monitor.enabled():return {'status':'Disabled'}
    review,source=_locked(name)
    if review.status!='Active':return {'status':'Paused'}
    with _as_responsible(review,source):
        if source.docstatus==2 and source.doctype not in {cases.controls.AUTH,cases.controls.RETRO}:
            _save_state(review,'Needs Review',_('Origen cancelado: conserve y revise el trabajo histórico antes de ampliar esta evaluación.'))
            return {'status':'Needs Review','cases':[]}
        options=cases._options(review.evaluation_options)
        result=cases.controls.preview(source.doctype,source.name,**options)
        rows=cases.record_result(source,options,result,review.responsible,review.name)
        _save_state(review,'Checked',_('Condiciones inscritas comprobadas; las incidencias nuevas quedan en seguimiento.'))
        return {'status':'Checked','cases':rows}


def _candidates(limit=10):
    table=frappe.qb.DocType(DT)
    return (frappe.qb.from_(table).select(table.name).where((table.docstatus==0)&(table.status=='Active'))
        .where(table.monitor_checked_on.isnull()|(table.monitor_checked_on<now_datetime()-timedelta(hours=1)))
        .orderby(table.monitor_checked_on).orderby(table.creation).orderby(table.name)
        .limit(max(1,min(cint(limit),30))).run(as_dict=True))


def scheduled_scan():
    if not monitor.enabled():return
    for row in _candidates():
        try:process_review(row.name);frappe.db.commit()
        except Exception as exc:
            trace=frappe.get_traceback();frappe.db.rollback()
            try:
                review=frappe.get_doc(DT,row.name,for_update=True)
                status='Access Required' if isinstance(exc,frappe.PermissionError) else 'Needs Review' if isinstance(exc,(frappe.ValidationError,ValueError)) else 'Error'
                _save_state(review,status,_('No se pudo completar la evaluación; revise el responsable y la evidencia.'))
                frappe.db.commit()
            except Exception:
                frappe.db.rollback();frappe.log_error(title='Working time review monitor',message=frappe.get_traceback())
            if not isinstance(exc,(frappe.ValidationError,frappe.PermissionError,ValueError)):
                frappe.log_error(title='Working time review monitor',message=trace)
