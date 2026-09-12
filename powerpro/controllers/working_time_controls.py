"""Permission-scoped live work-time diagnostics; no payroll or incident writes."""
from datetime import datetime,time,timedelta
from copy import deepcopy
import frappe
from frappe import _
from frappe.utils import getdate,get_datetime,now_datetime
from powerpro.controllers.overtime_source import AUTH,RETRO,evidence_enabled
from powerpro.controllers.checkin_overtime import _evidence_hash
from powerpro.payroll_rules.working_time_controls import evaluate
from powerpro.controllers.overtime_history import physical_input

NIGHT='Ordinary Night Settlement'


def _visible_checkins(names):
    names=set(names)
    if names:
        visible=set(frappe.get_list('Employee Checkin',filters={'name':['in',sorted(names)]},pluck='name',limit_page_length=len(names)))
        if visible!=names:frappe.throw(_('No tiene acceso a todas las marcaciones necesarias para estos controles.'),frappe.PermissionError)


def _quarter(doc):
    day=getdate(doc.work_date);month=1+3*((day.month-1)//3)
    start=datetime(day.year,month,1);end=datetime(day.year+1,1,1) if month==10 else datetime(day.year,month+3,1)
    intervals=[];sources=[];checkins=[];issues=[]
    from powerpro.controllers.overtime_history import compare
    for dt,mode in [(AUTH,['evidence_enrolled','=',1]),(RETRO,['reconciliation_engine','=','Verified Checkins'])]:
        rows=frappe.get_all(dt,filters=[['employee','=',doc.employee],['docstatus','in',[1,2]],mode,
            ['authorization_start','<',end],['authorization_end','>',start]],fields=['name'],limit=101)
        if rows and not frappe.has_permission(dt,'read'):frappe.throw(_('Falta acceso a los orígenes de evidencia del trimestre.'),frappe.PermissionError)
        if len(rows)>100:frappe.throw(_('El trimestre supera cien orígenes por tipo; requiere una revisión acotada.'))
        for row in rows:
            source=frappe.get_doc(dt,row.name);source.check_permission('read')
            try:
                comparison=compare(source)
                checkins.extend(r['name'] for r in comparison['current'].get('source_checkins',[]))
                if not comparison['matches']:
                    issues.append({'code':'quarter_evidence_changed','source_type':dt,'source_name':row.name});continue
                current=comparison['current']
                intervals.extend(current.get('calculation',{}).get('intervals',[]))
                sources.append({'source_type':dt,'source_name':row.name,'input_hash':current['input_hash'],
                    **({'history_revision':comparison['revision'].name} if comparison['revision'] else {})})
            except (frappe.ValidationError,ValueError):
                issues.append({'code':'quarter_evidence_incomplete','source_type':dt,'source_name':row.name})
    # Enrollment is not evidence of all overtime worked in the quarter, and
    # source reasons are free text rather than a certified Article153 category.
    return {'start':start,'end':end,'intervals':intervals,'sources':sources,'checkins':checkins,'issues':issues,'complete':False}


def _historical_current(doc):
    from powerpro.controllers.overtime_history import compare
    from powerpro.controllers.checkin_overtime_week import load_week
    from powerpro.payroll_rules.overtime_actual_week import collect_weekly_work
    comparison=compare(doc)
    current=deepcopy(comparison['current'])
    accepted=comparison['matches']
    current['state']='Verified' if accepted else 'Needs Review'
    current['historical_review']={'accepted':accepted,
        'revision':comparison['revision'].name if comparison['revision'] else None,
        'saved_physical_hash':_evidence_hash(physical_input(comparison['saved']))}
    employee=frappe.get_doc('Employee',doc.employee)
    data=load_week(doc,employee,current['input']['assignments'])
    historical=data.pop('historical_intervals',[]);names=data.pop('historical_checkins',[])
    certified=data.pop('certified_sessions',[])
    weekly=collect_weekly_work(**data,
        accepted_intervals=historical+(current.get('worked_intervals',[]) if accepted else []),
        accepted_checkins=names+([r['name'] for r in current.get('source_checkins',[])] if accepted else []),
        certified_sessions=certified+(current.get('certified_sessions',[]) if accepted else []))
    return current,weekly,current['input']['shift'],data['rows']


def _current(doc):
    if doc.docstatus==2 and doc.doctype in {AUTH,RETRO}:
        return _historical_current(doc)
    if doc.doctype!=NIGHT:
        from powerpro.controllers.checkin_overtime import build_result
        current=build_result(doc)
        return current,current.get('weekly_evidence') or {},current['input']['shift'],current['input']['weekly']['rows']
    from powerpro.controllers.ordinary_night import build_preview
    from powerpro.controllers.checkin_overtime_week import load_week
    from powerpro.payroll_rules.overtime_actual_week import collect_weekly_work
    current=build_preview(doc);context=current['input']['context']
    employee=frappe.get_doc('Employee',doc.employee)
    assignments=frappe.get_all('Shift Assignment',filters={'employee':doc.employee,'docstatus':1,'status':'Active',
        'start_date':['<=',getdate(doc.work_date)+timedelta(days=2)]},fields=['shift_type','start_date','end_date'],limit=1001)
    if len(assignments)>1000:frappe.throw(_('Demasiadas asignaciones de turno.'))
    start=get_datetime(context['shift_start']);end=max([get_datetime(context['shift_end'])]+[get_datetime(r['end']) for r in current['input']['extensions']])
    facade=frappe._dict(doctype=NIGHT,name=doc.name,employee=doc.employee,authorization_start=start,authorization_end=end,work_date=doc.work_date)
    data=load_week(facade,employee,assignments)
    historical=data.pop('historical_intervals',[]);historical_names=data.pop('historical_checkins',[]);certified=data.pop('certified_sessions',[])
    if current['input'].get('certified_session'):certified.append({'shift':current['input']['shift']['name'],'start':str(start),'end':str(context['shift_end'])})
    weekly=collect_weekly_work(**data,accepted_intervals=historical+current.get('worked_intervals',[]),
        accepted_checkins=historical_names+[r['name'] for r in current.get('source_checkins',[])],certified_sessions=certified)
    return current,weekly,current['input']['shift'],data['rows']


@frappe.whitelist()
def preview(source_type,source_name,profile='General',reference='',break_rule='One hour after four',quarterly_basis='Unclassified',rest_start=None,rest_end=None):
    if source_type not in {AUTH,RETRO,NIGHT}:frappe.throw(_('Origen de controles no admitido.'))
    doc=frappe.get_doc(source_type,source_name);doc.check_permission('read')
    frappe.get_doc('Employee',doc.employee).check_permission('read')
    if not frappe.has_permission('Employee Checkin','read'):frappe.throw(_('Necesita permiso de lectura de marcaciones.'),frappe.PermissionError)
    historical=doc.docstatus==2 and source_type in {AUTH,RETRO}
    if (doc.docstatus!=1 and not historical) or (source_type!=NIGHT and not evidence_enabled(doc)):
        frappe.throw(_('Seleccione un origen aprobado con conciliación por evidencia.'))
    try:
        current,weekly,shift,week_rows=_current(doc)
        quarter=_quarter(doc)
        _visible_checkins([r['name'] for r in current.get('source_checkins',[])]+[r['name'] for r in week_rows]+quarter['checkins'])
        start=weekly.get('start') or datetime.combine(getdate(doc.work_date)-timedelta(days=getdate(doc.work_date).weekday()),time.min)
        cutoff=weekly.get('cutoff') or doc.get('authorization_end') or current['input']['context']['shift_end']
        result=evaluate(worked_intervals=current.get('worked_intervals',[]),weekly_intervals=weekly.get('intervals',[]),
            session_complete=current['state']=='Verified',weekly_complete=bool(weekly.get('complete') and current['state']=='Verified'),
            week_start=start,cutoff=cutoff,profile=profile,reference=reference,break_rule=break_rule,
            breaks_observable=bool(current.get('manual_declaration') or current['input'].get('certified_session')
                or shift.get('working_hours_calculation_based_on')=='Every Valid Check-in and Check-out'),
            quarter_intervals=quarter['intervals'],quarter_start=quarter['start'],quarter_end=quarter['end'],quarter_complete=False,
            quarterly_basis=quarterly_basis,rest_start=rest_start,rest_end=rest_end)
    except ValueError as exc:frappe.throw(str(exc))
    if historical and not current['historical_review']['accepted']:
        for control in result['controls']:
            control['observed_status']=control['status']
            control['status']='Historical review required'
            control['message']=_('La evidencia histórica cambió o está incompleta; revise el trabajo antes de resolver este control.')
    # Separate proofs keep an unrelated quarterly change from invalidating a
    # decision about this session. Physical identity includes the original marks.
    def access(rows=(),sources=()):
        return ([{'document_type':'Employee Checkin','document_name':r['name']} for r in rows]
            +[{'document_type':r['source_type'],'document_name':r['source_name']} for r in sources if r.get('source_type') and r.get('source_name')]
            +[{'document_type':'Overtime Reconciliation Run','document_name':r['history_revision']} for r in sources if r.get('history_revision')])
    result['supporting_evidence']={
        'session':{'input':{**physical_input(current),**{k:current['input'][k] for k in ('context','extensions','certified_session') if k in current['input']}},'worked_intervals':current.get('worked_intervals',[]),
            'checkins':current.get('source_checkins',[]),'state':current['state'],
            'access':access(current.get('source_checkins',[]))},
        'weekly':{**weekly,'access':access(week_rows,weekly.get('issues',[]))
            +[{'document_type':'Attendance','document_name':n} for c in weekly.get('coverage',[]) for n in c.get('attendances',[])]},
        'quarter':{**{k:quarter[k] for k in ('start','end','intervals','sources','issues','complete')},
            'access':access([{'name':n} for n in quarter['checkins']],quarter['sources']+quarter['issues'])}}
    if historical:
        for key in ('session','weekly'):
            result['supporting_evidence'][key]['historical_review']=current['historical_review']
            if current['historical_review']['revision']:
                result['supporting_evidence'][key]['access'].append({'document_type':'Overtime Reconciliation Run',
                    'document_name':current['historical_review']['revision']})
    for part in result['supporting_evidence'].values():
        for ref in part.get('access',[]):
            if not frappe.has_permission(ref['document_type'],'read',doc=ref['document_name']):
                frappe.throw(_('Falta acceso a una referencia necesaria para evaluar la jornada.'),frappe.PermissionError)
    result.update(source_type=source_type,source_name=doc.name,employee=doc.employee,work_date=str(getdate(doc.work_date)),
        evaluated_on=str(now_datetime()),current_evidence_state=current['state'],quarter_sources=quarter['sources'],
        evidence_issues=list(current.get('issues',[]))+weekly.get('issues',[])+quarter['issues'],
        input_hash=_evidence_hash({'current':current['input_hash'],'weekly':weekly,'quarter':quarter,'controls':result}),
        notes=[_('Lectura actual con régimen seleccionado para evaluación; no equivale a su aprobación legal ni cambia horas o pagos.'),
            _('El trimestre incluye solo orígenes inscritos, accesibles y con evidencia vigente; su cobertura no está certificada.'),
            _('La semana se agrupa de lunes a domingo y el trimestre por calendario; confirme el período aplicable.'),
            _('La falta de marcaciones no acredita ausencia ni disfrute de descanso.')])
    if historical:
        result['historical_only']=True
        result['historical_review']=current['historical_review']
        result['notes'].append(_('El origen está cancelado: se evalúa el trabajo físico conservado, sin reabrir la liquidación.'))
    return result
