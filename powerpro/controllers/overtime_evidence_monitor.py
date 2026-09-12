"""Bounded monitoring of protected evidence; never rewrites work or finances."""
from contextlib import contextmanager
from datetime import timedelta
import hashlib
import frappe
from frappe import _
from frappe.utils import cint,flt,now_datetime
from powerpro.controllers import checkin_overtime as evidence
from powerpro.controllers.overtime_source import AUTH,RETRO
from powerpro.controllers.overtime import _reconciliation_rows

DT='Overtime Evidence Watch'
NIGHT='Ordinary Night Settlement'
SOURCES=(AUTH,RETRO,NIGHT)


def enabled():
    return bool(cint(evidence._settings().get('enable_overtime_evidence_monitor')))


def _access(doc):
    doc.check_permission('read')
    from powerpro.payroll_rules.manual_overtime import verification_roles
    if not verification_roles(evidence._settings().get('overtime_manual_verification_roles')).intersection(frappe.get_roles()):
        frappe.throw(_('Su rol no permite comprobar evidencia de horas extras.'),frappe.PermissionError)


def _source(source_type,name):
    if source_type not in SOURCES:frappe.throw(_('Origen de seguimiento no admitido.'))
    ref=frappe.get_doc(source_type,name);_access(ref)
    # Same order as reconciliation/review, so a monitor cannot freeze a mixture
    # of old source state and new financial state during an HR correction.
    if source_type==AUTH and ref.overtime_work_call:
        frappe.get_doc('Overtime Work Call',ref.overtime_work_call,for_update=True)
    frappe.db.get_value('Employee',ref.employee,'name',for_update=True)
    doc=frappe.get_doc(source_type,name,for_update=True);_access(doc)
    if doc.employee!=ref.employee or (source_type==AUTH and doc.overtime_work_call!=ref.overtime_work_call):
        frappe.throw(_('El origen cambió durante la comprobación. Reintente.'))
    if doc.docstatus not in {1,2} or not doc.evidence_snapshot:
        frappe.throw(_('El documento aún no tiene evidencia aprobada que vigilar.'))
    if source_type==AUTH and not doc.evidence_enrolled:frappe.throw(_('La autorización no está inscrita.'))
    if source_type==RETRO and doc.reconciliation_engine!='Verified Checkins':frappe.throw(_('El ajuste usa el motor anterior.'))
    return doc


def _dependencies(doc):
    if doc.doctype==NIGHT:
        rows=[]
        for dt in (AUTH,RETRO):
            references=_reconciliation_rows(dt,for_update=True,
                filters={'employee':doc.employee,'work_date':doc.work_date,'docstatus':1},fields=['name','settlement_status','evidence_snapshot'],limit=201)
            if len(references)>200:frappe.throw(_('Demasiadas dependencias nocturnas; requiere revisión.'))
            for row in references:
                snapshot=frappe.parse_json(row.evidence_snapshot or '{}')
                if (snapshot.get('ordinary_night_settlement') or {}).get('name')==doc.name:
                    rows.append({'doctype':dt,'name':row.name,'settlement_status':row.settlement_status,'blocks_reversal':row.settlement_status in evidence.FINAL})
    else:
        from powerpro.controllers.checkin_overtime_review import _dependencies as weekly_dependencies
        rows=weekly_dependencies(doc,for_update=True)
    return [r for r in rows if frappe.has_permission(r['doctype'],'read',doc=r['name'])]


def watch_permission(doc,ptype=None,user=None,**kwargs):
    if doc.source_type not in SOURCES:return False
    return frappe.has_permission(doc.source_type,'read',doc=doc.source_name,user=user)


def watch_query(user=None):
    return source_query('Overtime Evidence Watch',user)


def source_query(table,user=None):
    if table not in {'Overtime Evidence Watch','Working Time Incident'}:
        raise ValueError('Unsupported evidence table')
    from frappe.model.db_query import DatabaseQuery
    user=user or frappe.session.user
    if user=='Administrator':return ''
    clauses=[]
    for source_type in SOURCES:
        if not frappe.has_permission(source_type,'read',user=user):continue
        query=DatabaseQuery(source_type,user=user)
        query.fields=['name'];query.tables=['`tab'+source_type+'`']
        condition=query.build_match_conditions()
        clauses.append("(`tab"+table+"`.source_type="+frappe.db.escape(source_type)
            +" AND EXISTS(SELECT 1 FROM `tab"+source_type+"` WHERE `tab"+source_type+"`.name=`tab"+table+"`.source_name"
            +(' AND ('+condition+')' if condition else '')+'))')
    return '('+' OR '.join(clauses)+')' if clauses else '1=0'



def _evaluate(doc):
    saved=frappe.parse_json(doc.evidence_snapshot or '{}')
    old_hours=flt(doc.night_hours if doc.doctype==NIGHT else doc.verified_hours)
    values={'stored_hash':saved.get('input_hash'),'current_hash':None,'stored_hours':old_hours,'current_hours':None,
        'settlement_status':doc.settlement_status,'dependencies':evidence._json(_dependencies(doc))}
    if doc.doctype==NIGHT and doc.docstatus==2:
        return {**values,'status':'Current','summary':_('La liquidación nocturna está cancelada.'),'issues':'[]'}
    if doc.docstatus==2:
        from powerpro.controllers.overtime_history import compare
        from powerpro.controllers.checkin_overtime import _evidence_hash
        history=compare(doc,for_update=True);current=history['current'];saved=history['saved']
        issues=list(current['issues'])
        if history['revision']:issues.append({'code':'historical_evidence_revision','revision':history['revision'].name,'severity':'information'})
        if not history['matches']:issues.insert(0,{'code':'cancelled_physical_evidence_changed','message':_('Revise la evidencia física histórica del origen cancelado.')})
        from powerpro.controllers.overtime_history import physical_input
        return {**values,'stored_hash':_evidence_hash(physical_input(saved)),'current_hash':current['input_hash'],
            'stored_hours':flt((saved.get('snapshot') or {}).get('verified_hours')),
            'current_hours':flt((current.get('snapshot') or {}).get('verified_hours')),
            'status':'Current' if history['matches'] else 'Needs Review',
            'summary':_('La evidencia física histórica sigue vigente; la liquidación permanece cancelada.') if history['matches'] else _('Gestión Humana debe revisar el trabajo histórico y sus dependencias.'),
            'issues':evidence._json(issues)}
    try:
        if doc.doctype==NIGHT:
            from powerpro.controllers.ordinary_night import build_preview
            current=build_preview(doc,for_update=True)
            hours=flt(current.get('ordinary_hours'))
            ready=current['state']=='Verified'
            blockers=[]
        else:
            current=evidence.build_result(doc,for_update=True)
            hours=flt((current.get('snapshot') or {}).get('verified_hours'))
            ready=bool(current.get('settlement_ready'))
            blockers=current.get('settlement_blockers',[])
        changed=not saved.get('input_hash') or saved['input_hash']!=current['input_hash']
        issues=list(current.get('issues',[]))
        if changed:issues.insert(0,{'code':'protected_evidence_changed','message':_('La evidencia actual difiere de la instantánea guardada.')})
        if doc.docstatus==1:
            issues.extend({'code':'settlement_pending','message':message} for message in blockers)
        if changed or current['state']=='Needs Review' or (doc.docstatus==1 and doc.settlement_status in evidence.FINAL and not ready):
            status='Needs Review';summary=_('Gestión Humana debe revisar la evidencia y sus documentos dependientes.')
        elif current['state']!='Verified' or (doc.docstatus==1 and not ready):
            status='Waiting';summary=_('Faltan condiciones para completar la conciliación o liquidación.')
        else:
            status='Current';summary=_('La evidencia coincide con la instantánea guardada.')
        return {**values,'current_hash':current['input_hash'],'current_hours':hours,'status':status,'summary':summary,'issues':evidence._json(issues)}
    except frappe.ValidationError as exc:
        return {**values,'status':'Needs Review','summary':_('La comprobación requiere revisión.'),
            'issues':evidence._json([{'code':'evidence_validation','message':str(exc)[:2000]}])}


@contextmanager
def _writing():
    old=frappe.flags.get('overtime_evidence_monitor_write')
    frappe.flags.overtime_evidence_monitor_write=True
    try:yield
    finally:frappe.flags.overtime_evidence_monitor_write=old


def check_source(source_type,name):
    if not enabled():return {'status':'Disabled'}
    doc=_source(source_type,name)
    try:values=_evaluate(doc)
    except Exception:
        frappe.log_error(title='Overtime evidence monitor',message=frappe.get_traceback())
        values={'status':'Error','summary':_('No se pudo comprobar la evidencia; revise el registro de errores.'),
            'stored_hash':frappe.parse_json(doc.evidence_snapshot or '{}').get('input_hash'),'current_hash':None,
            'stored_hours':flt(doc.get('verified_hours') or doc.get('night_hours')),'current_hours':None,
            'settlement_status':doc.settlement_status,'issues':evidence._json([{'code':'evaluation_error'}]),'dependencies':'[]'}
    key=hashlib.sha256((source_type+'|'+name).encode()).hexdigest()
    existing=frappe.db.get_value(DT,{'source_key':key},'name',for_update=True)
    watch=frappe.get_doc(DT,existing,for_update=True) if existing else frappe.new_doc(DT)
    values.update(source_type=source_type,source_name=name,employee=doc.employee,company=doc.company,
        work_date=doc.work_date,source_key=key,responsible=doc.get('approver') or doc.get('approved_by'))
    changed=not existing or any(str(watch.get(k) if watch.get(k) is not None else '')!=str(v if v is not None else '') for k,v in values.items())
    if changed:
        watch.update(values);watch.checked_on=now_datetime();watch.changed_on=watch.checked_on
        with _writing():watch.save(ignore_permissions=True)
    else:
        watch.db_set('checked_on',now_datetime(),update_modified=False)
    return {'name':watch.name,'status':values['status'],'changed':changed}


def _candidates(limit=50):
    limit=max(1,min(cint(limit),100));cutoff=now_datetime()-timedelta(hours=1)
    watch=frappe.qb.DocType(DT);rows=[]
    for source_type in SOURCES:
        source=frappe.qb.DocType(source_type)
        query=(frappe.qb.from_(source).left_join(watch).on((watch.source_type==source_type)&(watch.source_name==source.name))
            .select(source.name,watch.checked_on).where(source.docstatus.isin([1,2]))
            .where(source.evidence_snapshot.isnotnull()).where(source.evidence_snapshot!='')
            .where(watch.name.isnull()|(watch.checked_on<cutoff)))
        if source_type==AUTH:query=query.where(source.evidence_enrolled==1)
        elif source_type==RETRO:query=query.where(source.reconciliation_engine=='Verified Checkins')
        query=query.orderby(watch.checked_on).orderby(source.name).limit(limit)
        rows.extend({'source_type':source_type,**r} for r in query.run(as_dict=True))
    rows.sort(key=lambda r:(str(r['checked_on'] or ''),r['source_type'],r['name']))
    return rows[:limit]


@frappe.whitelist(methods=['POST'])
def recheck(name):
    watch=frappe.get_doc(DT,name);watch.check_permission('read')
    return check_source(watch.source_type,watch.source_name)


def scheduled_check():
    if not enabled():return
    for candidate in _candidates():
        try:
            check_source(candidate['source_type'],candidate['name'])
            frappe.db.commit()
        except Exception:
            frappe.db.rollback()
            frappe.log_error(title='Overtime evidence monitor',message=frappe.get_traceback())
