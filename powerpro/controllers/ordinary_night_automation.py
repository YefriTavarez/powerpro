"""Bounded independent night processing with explicit per-employee enrollment."""
from contextlib import contextmanager
from datetime import timedelta
import frappe
from frappe import _
from frappe.utils import cint,getdate,now_datetime
from powerpro.controllers import ordinary_night as night
from powerpro.controllers.checkin_overtime import _json

DT='Ordinary Night Automation'
DAY='Ordinary Night Automation Day'
FINAL={'Created','Existing'}


def enabled():
    return bool(cint(frappe.db.get_single_value('DGII Payroll Settings','enable_checkin_overtime_reconciliation')))


@contextmanager
def _as_approver(doc):
    user=frappe.session.user
    if not doc.approved_by or not frappe.db.get_value('User',doc.approved_by,'enabled'):
        frappe.throw(_('El aprobador de la programación está deshabilitado.'))
    try:
        frappe.set_user(doc.approved_by)
        doc.check_permission('read');doc.check_permission('submit');night.check_role()
        yield
    finally:frappe.set_user(user)


def _evaluate(doc,row):
    doc.validate_policy()
    employee=frappe.get_doc('Employee',doc.employee)
    if employee.company!=doc.company:frappe.throw(_('La empresa del empleado cambió; revise la programación.'))
    if employee.date_of_joining and getdate(row.work_date)<getdate(employee.date_of_joining):
        frappe.throw(_('La fecha es anterior al ingreso del empleado.'))
    if employee.relieving_date and getdate(row.work_date)>getdate(employee.relieving_date):
        frappe.throw(_('La fecha es posterior a la salida del empleado.'))
    previous=frappe.get_all(night.DT,filters={'employee':doc.employee,'work_date':row.work_date},fields=['name','docstatus'],limit=101)
    if len(previous)>100:frappe.throw(_('Demasiadas revisiones nocturnas para esta jornada.'))
    active=[r for r in previous if r.docstatus==1]
    if len(active)>1:frappe.throw(_('Existen varias liquidaciones activas; requiere revisión.'))
    if active:
        existing=frappe.get_doc(night.DT,active[0].name);existing.check_permission('read')
        fresh=night.validate_fresh(existing)
        return {'status':'Existing','settlement':existing.name,'night_hours':fresh['ordinary_hours'],'amount':fresh['amount'],
            'input_hash':fresh['input_hash'],'summary':_('Se conserva la liquidación existente.'),'issues':'[]'}
    if previous:frappe.throw(_('Hay una liquidación en borrador o cancelada; resuélvala expresamente antes de reintentar.'))
    settlement=frappe.get_doc({'doctype':night.DT,'employee':doc.employee,'work_date':row.work_date,
        'settlement_payroll_date':doc.settlement_payroll_date,
        'review_reference':_('Programación automática {0}; aprobada por {1}.').format(doc.name,doc.approved_by)})
    result=night.build_preview(settlement,for_update=True)
    if result['input']['policy']['name']!=doc.policy:frappe.throw(_('La política de la jornada difiere de la programación aprobada.'))
    values={'night_hours':result['ordinary_hours'],'amount':result['amount'],'input_hash':result['input_hash'],'issues':_json(result['issues']), 'settlement':None}
    if result['state']!='Verified':
        return {**values,'status':'Waiting' if result['state']=='Waiting' else 'Needs Review',
            'summary':_('Esperando cierre o sincronización.') if result['state']=='Waiting' else _('La evidencia de la jornada requiere revisión.')}
    if result['amount']<=0:return {**values,'status':'No Premium','summary':_('La evidencia verificada no genera recargo nocturno ordinario.')}
    settlement.insert();settlement.submit();settlement.reload()
    return {**values,'status':'Created','settlement':settlement.name,'summary':_('Liquidación nocturna y salario adicional creados.')}


def process_day(schedule,work_date):
    if not enabled():return {'status':'Disabled'}
    ref=frappe.get_doc(DT,schedule)
    frappe.db.get_value('Employee',ref.employee,'name',for_update=True)
    doc=frappe.get_doc(DT,schedule,for_update=True)
    if doc.employee!=ref.employee:frappe.throw(_('La programación cambió; reintente.'))
    if doc.docstatus!=1 or not cint(doc.enabled):return {'status':'Paused'}
    row=next((r for r in doc.days if getdate(r.work_date)==getdate(work_date)),None)
    if not row:frappe.throw(_('La fecha no está inscrita en esta programación.'))
    if row.status in FINAL:return {'status':row.status,'settlement':row.settlement}
    if getdate(row.work_date)>getdate(now_datetime()):return {'status':'Waiting'}
    effective=frappe.db.get_single_value('DGII Payroll Settings','checkin_overtime_effective_from')
    if not effective or getdate(row.work_date)<getdate(effective):return {'status':'Disabled'}
    point='ordinary_auto_'+frappe.generate_hash(length=8);frappe.db.savepoint(point)
    try:
        with _as_approver(doc):values=_evaluate(doc,row)
    except Exception as exc:
        frappe.db.rollback(save_point=point)
        if isinstance(exc,(frappe.ValidationError,frappe.PermissionError,ValueError)):
            values={'status':'Needs Review','summary':str(exc)[:1500],'issues':_json([{'code':'validation','message':str(exc)[:2000]}])}
        else:
            frappe.log_error(title='Ordinary night automation',message=frappe.get_traceback())
            values={'status':'Error','summary':_('No se pudo procesar la jornada; revise el registro de errores.'),'issues':_json([{'code':'processing_error'}])}
    if values['status'] in {'Error','Needs Review'} and 'input_hash' not in values:
        values.update(input_hash=None,night_hours=0,amount=0,settlement=None)
    # These operational rows never replace the protected settlement evidence.
    try:frappe.db.set_value(DAY,row.name,{**values,'checked_on':now_datetime()},update_modified=False)
    except Exception:
        frappe.db.rollback(save_point=point)
        raise
    return {**values,'schedule':doc.name,'work_date':str(getdate(row.work_date))}


def _candidates(limit=30):
    parent=frappe.qb.DocType(DT);day=frappe.qb.DocType(DAY)
    effective=frappe.db.get_single_value('DGII Payroll Settings','checkin_overtime_effective_from')
    if not effective:return []
    return (frappe.qb.from_(day).join(parent).on(day.parent==parent.name)
        .select(parent.name,day.work_date).where((parent.docstatus==1)&(parent.enabled==1)&(day.parenttype==DT)&(day.parentfield=='days')
            &day.status.notin(list(FINAL))&(day.work_date>=getdate(effective))&(day.work_date<=getdate(now_datetime()))
            &(day.checked_on.isnull()|(day.checked_on<now_datetime()-timedelta(hours=1))))
        .orderby(day.checked_on).orderby(day.work_date).orderby(parent.name).limit(max(1,min(cint(limit),100))).run(as_dict=True))


def scheduled_check():
    if not enabled():return
    for row in _candidates():
        try:process_day(row.name,row.work_date);frappe.db.commit()
        except Exception:
            frappe.db.rollback();frappe.log_error(title='Ordinary night automation',message=frappe.get_traceback())


@frappe.whitelist(methods=['POST'])
def process_now(schedule):
    doc=frappe.get_doc(DT,schedule);doc.check_permission('write');night.check_role()
    return [process_day(schedule,row.work_date) for row in doc.days]
