"""Bounded incident checks and internal Alert notices; no payroll operations.

Scheduler owns each transaction. A failed evaluation/notice is fully rolled back
before storing its visible failure; realtime callbacks from rolled-back inserts
therefore cannot publish a notification for a nonexistent log.
"""
from contextlib import contextmanager
from datetime import timedelta
import frappe
from frappe import _
from frappe.utils import cint,get_datetime,now_datetime
from powerpro.controllers import working_time_incidents as cases
from powerpro.controllers.checkin_overtime import _evidence_hash

SETTINGS='DGII Payroll Settings'


def enabled():
    return bool(cint(frappe.db.get_single_value(SETTINGS,'enable_working_time_incident_monitor')))


def validate_settings(settings):
    if settings.get('enable_working_time_incident_notices') and not settings.get('enable_working_time_incident_monitor'):
        frappe.throw(_('Active la vigilancia de incidencias antes de habilitar sus avisos.'))
    value=settings.get('working_time_incident_reminder_days')
    try:
        days=float(value or 0);valid=days==int(days) and 0<=days<=30
    except (TypeError,ValueError,OverflowError):valid=False
    if not valid:frappe.throw(_('Los recordatorios deben configurarse entre cero y treinta días enteros.'))


@contextmanager
def _as_responsible(doc,source):
    original=frappe.session.user
    try:
        if not doc.responsible or not frappe.db.get_value('User',doc.responsible,'enabled'):
            frappe.throw(_('El responsable de la incidencia está deshabilitado.'),frappe.PermissionError)
        cases._responsible(source,doc.responsible)
        frappe.set_user(doc.responsible)
        doc.check_permission('read');cases._access(source)
        yield
    finally:frappe.set_user(original)


def _notice_reason(doc):
    if doc.status!='Open':return None
    options=cases._options(doc.evaluation_options)
    if (doc.control_code=='weekly_continuous_rest' and options.get('rest_end')
            and get_datetime(options['rest_end'])<now_datetime()):return 'Rest window elapsed'
    return 'Open incident'


def _notify(doc):
    if not cint(frappe.db.get_single_value(SETTINGS,'enable_working_time_incident_notices')):
        return {'notice_status':'Disabled'}
    reason=_notice_reason(doc)
    if not reason:return {'notice_status':'No open case'}
    from frappe.desk.doctype.notification_settings.notification_settings import is_notifications_enabled
    if not is_notifications_enabled(doc.responsible):return {'notice_status':'User muted'}
    key=_evidence_hash({'incident':doc.name,'evidence':doc.evidence_hash,'responsible':doc.responsible,'reason':reason})
    days=cint(frappe.db.get_single_value(SETTINGS,'working_time_incident_reminder_days'))
    due=bool(0<days<=30 and doc.last_notice_on and get_datetime(doc.last_notice_on)+timedelta(days=days)<=now_datetime())
    if doc.last_notice_key==key and not due:return {'notice_status':'Unchanged'}
    # Minimal text remains non-sensitive if access is revoked after delivery.
    # Native Alert explicitly bypasses email; honor native notification opt-out.
    subject=_('Descanso previsto vencido: hay una incidencia pendiente de revisar.') if reason=='Rest window elapsed' else _('Tiene una incidencia de jornada pendiente de revisión.')
    notice=frappe.get_doc({'doctype':'Notification Log','for_user':doc.responsible,'from_user':frappe.session.user,
        'type':'Alert','subject':subject,'document_type':cases.DT,'document_name':doc.name})
    notice.insert(ignore_permissions=True)
    return {'notice_status':'Sent','last_notice_key':key,'last_notice_on':now_datetime(),'last_notice':notice.name}


def _save_state(doc,values):
    checked=now_datetime()
    changed=any(str(doc.get(k) or '')!=str(v or '') for k,v in values.items())
    if changed:
        doc.update({**values,'monitor_checked_on':checked})
        with cases._writing():doc.save(ignore_permissions=True)
    else:doc.db_set('monitor_checked_on',checked,update_modified=False)


def process_incident(name):
    """Internal transactional operation; caller must commit or fully rollback."""
    if not enabled():return {'status':'Disabled'}
    doc,source=cases._locked(name)
    if doc.working_time_review:
        state=frappe.db.get_value('Working Time Review',doc.working_time_review,'status')
        if state=='Paused':return {'name':doc.name,'status':'Paused'}
        if state!='Active':frappe.throw(_('Falta la evaluación inscrita de esta incidencia.'))
    with _as_responsible(doc,source):
        result=cases._refresh(doc,source)
        notices=_notify(doc)
        status='Needs Review' if doc.status=='Open' else 'Current'
        _save_state(doc,{'monitor_status':status,'monitor_message':_('Comprobación periódica completada.'),**notices})
    return {**result,'monitor_status':status,'notice_status':notices['notice_status']}


def _record_failure(name,exc):
    # This transaction follows a full rollback and never recomputes or waives
    # source evidence. Lock only the case while recording operational status.
    doc=frappe.get_doc(cases.DT,name,for_update=True)
    if isinstance(exc,frappe.PermissionError):
        status='Access Required';message=_('Revise el responsable, sus roles y el acceso a los documentos de respaldo.')
    elif isinstance(exc,(frappe.ValidationError,ValueError)):
        status='Needs Review';message=_('La evidencia no pudo evaluarse; requiere revisión de Gestión Humana.')
    else:status='Error';message=_('Falló la comprobación automática; revise el registro de errores.')
    _save_state(doc,{'monitor_status':status,'monitor_message':message,'notice_status':'Not sent'})
    return status


def _candidates(limit=30):
    table=frappe.qb.DocType(cases.DT);review=frappe.qb.DocType('Working Time Review')
    return (frappe.qb.from_(table).left_join(review).on(table.working_time_review==review.name)
        .select(table.name).where(table.docstatus==0).where(review.name.isnull()|(review.status=='Active'))
        .where(table.monitor_checked_on.isnull()|(table.monitor_checked_on<now_datetime()-timedelta(hours=1)))
        .orderby(table.monitor_checked_on).orderby(table.creation).orderby(table.name)
        .limit(max(1,min(cint(limit),100))).run(as_dict=True))


def scheduled_check():
    if not enabled():return
    from powerpro.controllers.working_time_reviews import scheduled_scan
    scheduled_scan()
    for row in _candidates():
        try:
            process_incident(row.name);frappe.db.commit()
        except Exception as exc:
            trace=frappe.get_traceback();frappe.db.rollback()
            try:
                _record_failure(row.name,exc);frappe.db.commit()
            except Exception:
                frappe.db.rollback();frappe.log_error(title='Working time incident monitor',message=frappe.get_traceback())
            if not isinstance(exc,(frappe.ValidationError,frappe.PermissionError,ValueError)):
                frappe.log_error(title='Working time incident monitor',message=trace)
