"""Audited work-time cases. Resolutions never change evidence or earnings."""
from contextlib import contextmanager
import frappe
from frappe import _
from frappe.utils import get_datetime,now_datetime
from powerpro.controllers import working_time_controls as controls
from powerpro.controllers import overtime_evidence_monitor as monitor
from powerpro.controllers.checkin_overtime import _evidence_hash,_json

DT='Working Time Incident'
CLEAR='Within evaluated limit'
DEFAULTS=dict(profile='General',reference='',break_rule='One hour after four',quarterly_basis='Unclassified',rest_start=None,rest_end=None)


REFERENCE_TYPES=(*monitor.SOURCES,'Employee Checkin','Attendance')


def incident_query(user=None):
    from frappe.model.db_query import DatabaseQuery
    user=user or frappe.session.user
    if not frappe.has_permission('Employee Checkin','read',user=user):return '1=0'
    base=monitor.source_query(DT,user)
    if user=='Administrator':return base
    allowed=[]
    refs='`tabWorking Time Evidence Reference`'
    for dt in REFERENCE_TYPES:
        if not frappe.has_permission(dt,'read',user=user):continue
        query=DatabaseQuery(dt,user=user);query.fields=['name'];query.tables=['`tab'+dt+'`']
        condition=query.build_match_conditions()
        allowed.append('('+refs+'.document_type='+frappe.db.escape(dt)
            +' AND EXISTS(SELECT 1 FROM `tab'+dt+'` WHERE `tab'+dt+'`.name='+refs+'.document_name'
            +(' AND ('+condition+')' if condition else '')+'))')
    permitted=' OR '.join(allowed) or '1=0'
    references='NOT EXISTS(SELECT 1 FROM '+refs+' WHERE '+refs+'.parent=`tabWorking Time Incident`.name'
    references+=" AND "+refs+".parenttype='Working Time Incident' AND "+refs+".parentfield='evidence_references'"
    references+=' AND NOT ('+permitted+'))'
    return '('+(base or '1=1')+') AND '+references


def incident_permission(doc,ptype=None,user=None,**kwargs):
    return (frappe.has_permission('Employee Checkin','read',user=user)
        and monitor.watch_permission(doc,ptype,user) and bool(doc.employee)
        and frappe.has_permission('Employee','read',doc=doc.employee,user=user)
        and all(r.document_type in REFERENCE_TYPES and frappe.has_permission(r.document_type,'read',doc=r.document_name,user=user)
            for r in (doc.get('evidence_references') or [])))


def _options(value):
    value=frappe.parse_json(value) if isinstance(value,str) else value
    if not isinstance(value,dict) or set(value)-set(DEFAULTS):frappe.throw(_('Condiciones de evaluación inválidas.'))
    result={**DEFAULTS,**value}
    result['reference']=str(result['reference'] or '').strip()
    for key in ('rest_start','rest_end'):
        result[key]=str(get_datetime(result[key])) if result[key] else None
    return result


def _access(source):
    monitor._access(source)
    frappe.get_doc('Employee',source.employee).check_permission('read')
    if not frappe.has_permission(DT,'read'):frappe.throw(_('Necesita acceso al seguimiento de incidencias.'),frappe.PermissionError)


def _responsible(source,user):
    if not frappe.db.get_value('User',user,'enabled'):frappe.throw(_('Seleccione un responsable activo.'))
    from powerpro.payroll_rules.manual_overtime import verification_roles
    if not verification_roles(monitor.evidence._settings().get('overtime_manual_verification_roles')).intersection(frappe.get_roles(user)):
        frappe.throw(_('El responsable necesita un rol configurado para revisar evidencia.'),frappe.PermissionError)
    for dt,name in [(source.doctype,source.name),('Employee',source.employee),(DT,None)]:
        if not frappe.has_permission(dt,'read',doc=name,user=user):
            frappe.throw(_('El responsable necesita acceso al origen, al empleado y a las incidencias.'),frappe.PermissionError)


@contextmanager
def _writing():
    old=frappe.flags.get('working_time_incident_write');frappe.flags.working_time_incident_write=True
    try:yield
    finally:frappe.flags.working_time_incident_write=old


def _period(control):
    return str(get_datetime(control['start'])) if control.get('start') else None


def _proof(result,control,options):
    code=control['code'];support=result.get('supporting_evidence') or {}
    keys=('weekly',) if code=='weekly_work' else ('quarter',) if code=='quarterly_extension' else ('session','weekly') if code=='weekly_continuous_rest' else ('session',)
    # Options are immutable per scenario. Evidence is scoped to this control.
    return dict(version=result['version'],source_type=result['source_type'],source_name=result['source_name'],
        employee=result['employee'],work_date=result['work_date'],options=options,control=control,
        supporting_evidence={k:support.get(k) for k in keys})


def _update(doc,proof):
    digest=_evidence_hash(proof);control=proof['control'];changed=doc.evidence_hash!=digest
    doc.checked_on=now_datetime()
    if changed:
        was_closed=doc.status in ('Resolved','Documented Exception')
        doc.status='Open';doc.evidence_hash=digest;doc.evidence_snapshot=_json(proof)
        if 'supporting_evidence' in proof:
            references=sorted({(r['document_type'],r['document_name'])
                for value in proof['supporting_evidence'].values() if value
                for r in value.get('access',[])})
            doc.set('evidence_references',[])
            for dt,name in references:
                if dt not in REFERENCE_TYPES or not frappe.has_permission(dt,'read',doc=name):
                    frappe.throw(_('No tiene acceso a todas las referencias del control.'),frappe.PermissionError)
                doc.append('evidence_references',dict(document_type=dt,document_name=name))
        doc.evaluation_status=control['status'];doc.summary=control.get('message')
        doc.changed_on=doc.checked_on
        doc.change_reason=_('La evidencia cambió; se reabre la revisión y se conserva la resolución anterior.') if was_closed else _('Comprobación de evidencia actualizada.')
    if doc.is_new() or changed:
        with _writing():doc.save(ignore_permissions=True)
    else:doc.db_set('checked_on',doc.checked_on,update_modified=False)
    return {'name':doc.name,'status':doc.status,'evidence_hash':doc.evidence_hash,'changed':changed}


@frappe.whitelist(methods=['POST'])
def record(source_type,source_name,options,responsible,expected_hash):
    """One idempotent case per source/scenario/control/calendar period."""
    source=monitor._source(source_type,source_name);_access(source);_responsible(source,responsible)
    options=_options(options);result=controls.preview(source_type,source_name,**options)
    if not expected_hash or result['input_hash']!=expected_hash:frappe.throw(_('La evaluación cambió; consulte los controles nuevamente.'))
    records=[]
    for control in result['controls']:
        key=_evidence_hash(dict(source_type=source_type,source_name=source_name,options=options,code=control['code'],period=_period(control)))
        name=frappe.db.get_value(DT,{'incident_key':key},'name',for_update=True)
        if not name and control['status']==CLEAR:continue
        doc=frappe.get_doc(DT,name,for_update=True) if name else frappe.new_doc(DT)
        if name:doc.check_permission('read')
        if not name:
            doc.update(dict(source_type=source_type,source_name=source_name,employee=source.employee,company=source.company,
                work_date=source.work_date,control_code=control['code'],period_start=_period(control),
                incident_key=key,evaluation_options=_json(options),responsible=responsible,status='Open'))
        # Repeating a scenario cannot silently reassign its existing cases.
        records.append(_update(doc,_proof(result,control,options)))
    return records


def _locked(name):
    ref=frappe.get_doc(DT,name);ref.check_permission('read')
    source=monitor._source(ref.source_type,ref.source_name);_access(source)
    doc=frappe.get_doc(DT,name,for_update=True);doc.check_permission('read')
    if (doc.source_type,doc.source_name,doc.employee)!=(source.doctype,source.name,source.employee):
        frappe.throw(_('El origen de la incidencia cambió; requiere revisión.'))
    return doc,source


def _refresh(doc,source):
    options=_options(doc.evaluation_options)
    if source.docstatus==2:
        # Financial cancellation cannot certify disappearance of physical work.
        proof={'source_type':source.doctype,'source_name':source.name,'docstatus':2,'options':options,
            'control':{'code':doc.control_code,'status':'Historical review required',
                'message':_('Origen cancelado: conserve y revise la evidencia histórica; cancelar el pago no resuelve este control.')}}
        return _update(doc,proof)
    result=controls.preview(source.doctype,source.name,**options)
    matches=[c for c in result['controls'] if c['code']==doc.control_code and _period(c)==(str(doc.period_start) if doc.period_start else None)]
    if matches:control=matches[0]
    elif doc.control_code=='session_evidence' and result['current_evidence_state']=='Verified':
        control={'code':doc.control_code,'status':CLEAR,'message':_('La jornada ya tiene evidencia completa.')}
    else:control={'code':doc.control_code,'status':'Incomplete','message':_('El período original no está cubierto por la evaluación actual; requiere revisión.')}
    return _update(doc,_proof(result,control,options))


@frappe.whitelist(methods=['POST'])
def recheck(name):
    doc,source=_locked(name)
    return _refresh(doc,source)


@frappe.whitelist(methods=['POST'])
def resolve(name,expected_hash,resolution,reason,reference):
    doc,source=_locked(name)
    _refresh(doc,source)
    if not expected_hash or expected_hash!=doc.evidence_hash:frappe.throw(_('La evidencia cambió; compruebe y revise la incidencia antes de resolverla.'))
    if resolution not in {'Resolved','Documented Exception'}:frappe.throw(_('Seleccione una resolución válida.'))
    reason=str(reason or '').strip();reference=str(reference or '').strip()
    if not reason or not reference:frappe.throw(_('Indique la justificación y la referencia de la resolución.'))
    if resolution=='Resolved' and doc.evaluation_status!=CLEAR:
        frappe.throw(_('La evidencia actual todavía no demuestra que se resolvió este control.'))
    if resolution=='Documented Exception' and doc.evaluation_status not in {'Review','Documented regime required'}:
        frappe.throw(_('Una excepción no completa evidencia faltante ni acredita disfrute de descanso.'))
    if doc.status!='Open':frappe.throw(_('La incidencia ya tiene una resolución para esta evidencia.'))
    doc.update(dict(status=resolution,resolution_reason=reason,resolution_reference=reference,resolved_by=frappe.session.user,
        resolved_on=now_datetime(),resolved_hash=doc.evidence_hash,changed_on=now_datetime(),
        change_reason=_('Resolución documentada; conserva las horas y las obligaciones de pago.')))
    with _writing():doc.save(ignore_permissions=True)
    return {'name':doc.name,'status':doc.status}


@frappe.whitelist(methods=['POST'])
def assign(name,responsible,reason):
    doc,source=_locked(name);_responsible(source,responsible)
    reason=str(reason or '').strip()
    if not reason:frappe.throw(_('Explique el motivo de la asignación.'))
    if doc.responsible==responsible:return {'name':doc.name,'changed':False}
    doc.update(dict(responsible=responsible,change_reason=reason,changed_on=now_datetime()))
    with _writing():doc.save(ignore_permissions=True)
    return {'name':doc.name,'changed':True}
