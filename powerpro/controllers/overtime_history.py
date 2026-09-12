"""Append-only corrections of physical work from cancelled evidence sources.

A historical revision never reopens its source or creates/reverses money/leave.
Only the current verified physical session may contribute to later weekly work.
"""
from copy import deepcopy
from datetime import time,timedelta
import hashlib
import frappe
from frappe import _
from frappe.utils import cint,flt,now_datetime,get_datetime
from powerpro.controllers.overtime_source import AUTH,RETRO,evidence_enabled,links
from powerpro.controllers.overtime import _reconciliation_rows

APPLIED='Cancelled Work Evidence Reviewed'
PHYSICAL_KEYS=('calculator_version','authorization','rows','shift','contexts','next_windows','assignments','default_shift','manual_declaration','observation_window')


def physical_input(saved):
    return {k:v for k,v in (saved.get('input') or {}).items() if k in PHYSICAL_KEYS}


def latest(doc,*,for_update=False):
    if doc.docstatus!=2:return None
    rows=_reconciliation_rows('Overtime Reconciliation Run',for_update=for_update,
        filters={**links(doc),'result_status':APPLIED},fields=['name','history_sequence','evidence'],
        order_by='history_sequence desc, creation desc, name desc',limit=1)
    return rows[0] if rows else None


def effective_snapshot(doc,*,for_update=False):
    revision=latest(doc,for_update=for_update)
    if revision:return frappe.parse_json(revision.evidence)['after'],revision
    return frappe.parse_json(doc.evidence_snapshot or '{}'),None


def evaluate(doc,*,for_update=False,manual_declaration=None,observation_window=None):
    from powerpro.controllers.checkin_overtime import _data,_evidence_hash,now_datetime as evidence_now
    from powerpro.payroll_rules.overtime_evidence import evaluate_evidence
    from powerpro.payroll_rules.overtime_manual_session import evaluate_manual_session
    data,_settings=_data(doc,for_update=for_update,include_weekly=False,observation_window=observation_window)
    # A cancelled document claims no authorization window. A live replacement
    # does not invalidate its physical punches solely by overlapping its dates.
    competing=data['competing'] if doc.docstatus!=2 else False
    if manual_declaration is None:
        result=evaluate_evidence(authorization=data['authorization'],rows=data['rows'],shift=data['shift'],contexts=data['contexts'],
            next_windows=data['next_windows'],now=evidence_now(),competing=competing,night_start=time(21),night_end=time(7),observation_window=data.get('observation_window'))
    else:
        result=evaluate_manual_session(declaration=manual_declaration,authorization=data['authorization'],rows=data['rows'],
            contexts=data['contexts'],now=evidence_now(),competing=competing,night_start=time(21),night_end=time(7),observation_window=data.get('observation_window'))
        data['manual_declaration']=manual_declaration
    result['input']={k:v for k,v in data.items() if k in PHYSICAL_KEYS}
    result['input_hash']=_evidence_hash(result['input'])
    return result


def _acceptable(result):
    # Physical evidence may show zero authorized OT or extra unapproved time;
    # this service recognizes work only, and grants no authorization or payment.
    return bool(result.get('worked_intervals') and result['state'] in {'Verified','Needs Review'}
        and all(i['code']=='worked_authorized_mismatch' or i.get('severity')=='information' for i in result['issues']))


def compare(doc,*,for_update=False):
    from powerpro.controllers.checkin_overtime import _evidence_hash
    saved,revision=effective_snapshot(doc,for_update=for_update)
    declaration=(saved.get('review') or {}).get('manual_declaration')
    current=evaluate(doc,for_update=for_update,manual_declaration=declaration,observation_window=physical_input(saved).get('observation_window'))
    same=bool(saved.get('worked_intervals') and _evidence_hash(physical_input(saved))==current['input_hash']
        and _evidence_hash(saved.get('source_checkins'))==_evidence_hash(current.get('source_checkins'))
        and _evidence_hash(saved.get('worked_intervals'))==_evidence_hash(current.get('worked_intervals')))
    accepted=_acceptable(current) and (current['state']=='Verified' or bool(saved.get('review')))
    return {'saved':saved,'current':current,'revision':revision,'matches':bool(same and accepted)}


def _access(doc):
    from powerpro.controllers.checkin_overtime import _access as access,_settings
    access(doc)
    if doc.doctype not in {AUTH,RETRO} or doc.docstatus!=2 or not evidence_enabled(doc) or not doc.evidence_snapshot:
        frappe.throw(_('Esta acción requiere un origen cancelado con evidencia inscrita.'))
    settings=_settings()
    if not (cint(settings.get('enable_checkin_overtime_reconciliation')) or cint(settings.get('enable_overtime_evidence_monitor'))):
        frappe.throw(_('Habilite la revisión de marcaciones o su seguimiento para registrar una corrección histórica.'))
    if doc.doctype==RETRO and doc.approver!=frappe.session.user:
        frappe.throw(_('Solo el aprobador asignado puede revisar la evidencia histórica de este ajuste.'),frappe.PermissionError)


def _no_active_outputs(doc,*,for_update=False):
    from powerpro.controllers.overtime_cash_settlement import _get_linked_additional_salaries
    if _get_linked_additional_salaries(doc,docstatus=1,for_update=for_update) or _reconciliation_rows('Overtime Compensatory Credit',
        for_update=for_update,filters={**links(doc,authorization_field='overtime_authorization'),'docstatus':1},pluck='name',limit=1):
        frappe.throw(_('Complete primero la reversión de los efectos financieros del origen cancelado.'))


def _hours(snapshot):
    return round(sum((get_datetime(r['end'])-get_datetime(r['start'])).total_seconds()/3600 for r in snapshot.get('worked_intervals',[])),4)


def _expanded_dependencies(doc,window,*,for_update=False):
    """Include overlaps and later weekly results on both sides of an expansion."""
    start,end=get_datetime(window['start']),get_datetime(window['end'])
    last=end.date()+timedelta(days=7-end.weekday())
    found=[]
    for dt in (AUTH,RETRO):
        rows=_reconciliation_rows(dt,for_update=for_update,filters=[['employee','=',doc.employee],['docstatus','=',1],
            ['authorization_end','>',start],['authorization_start','<',last]],
            fields=['name','settlement_status'],order_by='authorization_start asc,name asc',limit=201)
        if len(rows)>200:frappe.throw(_('Demasiadas dependencias de la ventana histórica; requiere revisión acotada.'))
        for row in rows:
            found.append(dict(doctype=dt,name=row.name,settlement_status=row.settlement_status,
                blocks_reversal=row.settlement_status in {'Created','Payroll Submitted','Paid','Credited'},
                reason='expanded_historical_window'))
    nights=_reconciliation_rows('Ordinary Night Settlement',for_update=for_update,
        filters={'employee':doc.employee,'docstatus':1,'work_date':['between',[start.date()-timedelta(days=1),end.date()]]},
        fields=['name','settlement_status','evidence_snapshot'],order_by='name asc',limit=201)
    if len(nights)>200:frappe.throw(_('Demasiadas liquidaciones nocturnas dependientes.'))
    for row in nights:
        snapshot=frappe.parse_json(row.evidence_snapshot or '{}');data=snapshot.get('input') or {};context=data.get('context') or {}
        spans=list(snapshot.get('worked_intervals') or [])+list(data.get('extensions') or [])
        if context.get('shift_start') and context.get('shift_end'):
            spans.append({'start':context['shift_start'],'end':context['shift_end']})
        if not spans or any(get_datetime(r['start'])<end and get_datetime(r['end'])>start for r in spans):
            found.append(dict(doctype='Ordinary Night Settlement',name=row.name,settlement_status=row.settlement_status,
                blocks_reversal=row.settlement_status in {'Created','Payroll Submitted','Paid'},reason='expanded_historical_window'))
    return found


def _references(snapshot,revision=None):
    for row in snapshot.get('source_checkins',[]):
        if not frappe.has_permission('Employee Checkin','read',doc=row['name']):
            frappe.throw(_('Falta acceso a una marcación de la ventana histórica.'),frappe.PermissionError)
    if revision and not frappe.has_permission('Overtime Reconciliation Run','read',doc=revision.name):
        frappe.throw(_('Falta acceso a la revisión histórica anterior.'),frappe.PermissionError)


def _preview(doc,reason,manual_declaration=None,*,for_update=False,observation_window=None):
    from powerpro.controllers.checkin_overtime import _evidence_hash,_json,_settings
    from powerpro.controllers.checkin_overtime_review import _dependencies,_financial
    if not isinstance(reason,str) or not 1<=len(reason.strip())<=2000:frappe.throw(_('Documente el motivo de la corrección histórica.'))
    if isinstance(manual_declaration,str):manual_declaration=frappe.parse_json(manual_declaration)
    if manual_declaration is not None and not cint(_settings().get('enable_manual_overtime_verification')):
        frappe.throw(_('La declaración manual está desactivada.'))
    _no_active_outputs(doc,for_update=for_update)
    saved,revision=effective_snapshot(doc,for_update=for_update)
    previous_window=physical_input(saved).get('observation_window')
    if isinstance(observation_window,str):observation_window=frappe.parse_json(observation_window)
    if observation_window is None:observation_window=previous_window
    _references(saved,revision)
    try:
        if previous_window:
            from powerpro.payroll_rules.overtime_observation_window import normalize_window
            observation_window=normalize_window(observation_window,previous_window['start'],previous_window['end'])
        current=evaluate(doc,for_update=for_update,manual_declaration=manual_declaration,observation_window=observation_window)
    except ValueError as exc:frappe.throw(str(exc))
    _references(current)
    if not _acceptable(current):frappe.throw(_('Complete la evidencia física y resuelva marcaciones faltantes o ambiguas antes de aceptar.'))
    if (_evidence_hash(physical_input(saved))==current['input_hash']
            and _evidence_hash(saved.get('worked_intervals'))==_evidence_hash(current.get('worked_intervals'))
            and (current['state']=='Verified' or saved.get('review'))):
        frappe.throw(_('La evidencia física no cambió; no hace falta otra revisión histórica.'))
    dependencies=_dependencies(doc,for_update=for_update)
    if current['input'].get('observation_window'):
        expanded=_expanded_dependencies(doc,current['input']['observation_window'],for_update=for_update)
        dependencies=sorted({(r['doctype'],r['name']):r for r in dependencies+expanded}.values(),key=lambda r:(r['doctype'],r['name']))
    for row in dependencies:
        if not frappe.has_permission(row['doctype'],'read',doc=row['name']):
            frappe.throw(_('Falta acceso a una liquidación dependiente de la revisión histórica.'),frappe.PermissionError)
    stable={**links(doc),'reason':reason.strip(),'before':_evidence_hash(saved),'revision':revision.name if revision else None,
        'after':current['input_hash'],'after_worked':_evidence_hash(current.get('worked_intervals')),'dependencies':dependencies,'financial_before':_financial(doc)}
    token=hashlib.sha256(_json(stable).encode()).hexdigest()
    return {**stable,'token':token,'saved':saved,'current':current,'sequence':cint(revision.history_sequence) if revision else 0}


@frappe.whitelist()
def preview_review(authorization,reason,manual_declaration=None,source_type=AUTH,observation_window=None):
    if source_type not in {AUTH,RETRO}:frappe.throw(_('Origen histórico no admitido.'))
    doc=frappe.get_doc(source_type,authorization);_access(doc)
    p=_preview(doc,reason,manual_declaration,observation_window=observation_window)
    return {'token':p['token'],**links(doc),'reason':p['reason'],'before':p['saved'].get('snapshot',{}),
        'after':p['current'].get('snapshot',{}),'worked_hours_before':_hours(p['saved']),'worked_hours_after':_hours(p['current']),
        'financial_before':p['financial_before'],'proposed_amount':None,'historical_only':True,'dependencies':p['dependencies'],
        'settlement_ready':False,'settlement_blockers':[_('La revisión no reabre ni liquida este documento cancelado.')],
        'manual_declaration':p['current'].get('manual_declaration'),'checkin_comparison':{'source_checkins':p['current']['source_checkins']},
        'observation_window':p['current']['input'].get('observation_window'),
        'unapproved_hours':p['current'].get('calculation',{}).get('unapproved_hours',0)}


@frappe.whitelist(methods=['POST'])
def apply_review(authorization,reason,token,manual_declaration=None,source_type=AUTH,observation_window=None):
    from powerpro.controllers.overtime_rest import _lock_source
    from powerpro.controllers.checkin_overtime import _json
    doc,_call=_lock_source(authorization,allow_cancelled=True,source_type=source_type);_access(doc)
    existing=_reconciliation_rows('Overtime Reconciliation Run',for_update=True,
        filters={**links(doc),'result_status':APPLIED,'evidence_hash':token},pluck='name',limit=1)
    if existing:return {'status':'Applied','audit':existing[0],'idempotent':True}
    p=_preview(doc,reason,manual_declaration,for_update=True,observation_window=observation_window)
    if not token or token!=p['token']:frappe.throw(_('La evidencia histórica cambió; obtenga una vista previa nueva.'))
    blocked=[r for r in p['dependencies'] if r['blocks_reversal']]
    if blocked:frappe.throw(_('Resuelva primero las liquidaciones dependientes: {0}.').format(', '.join(r['name'] for r in blocked)))
    after=deepcopy(p['current']);review={'reason':p['reason'],'reviewed_by':frappe.session.user,'reviewed_on':str(now_datetime()),
        'request_token':token,'input_hash':after['input_hash']}
    if after.get('manual_declaration'):review['manual_declaration']=after['manual_declaration']
    after['review']=review;after['state']='Verified'
    for issue in after['issues']:
        if issue['code']=='worked_authorized_mismatch':issue.update(severity='information',accepted_by_hr=True)
    record=frappe.new_doc('Overtime Reconciliation Run')
    record.update({**links(doc),'employee':doc.employee,'work_date':doc.work_date,'result_status':APPLIED,
        'history_sequence':p['sequence']+1,'evidence_hash':token,'evaluated_by':frappe.session.user,'evaluated_on':now_datetime(),
        'evidence':_json({'before':p['saved'],'after':after,'dependencies':p['dependencies'],'previous_revision':p['revision'],
            'financial_before':p['financial_before'],'historical_only':True}),'issues':_json(after['issues'])})
    record.name=frappe.generate_hash(length=16);record.db_insert()
    return {'status':'Applied','audit':record.name,'history_sequence':record.history_sequence,'historical_only':True}


@frappe.whitelist()
def get_status(authorization,source_type=AUTH):
    if source_type not in {AUTH,RETRO}:frappe.throw(_('Origen histórico no admitido.'))
    doc=frappe.get_doc(source_type,authorization);doc.check_permission('read')
    if doc.docstatus!=2 or not evidence_enabled(doc):return {'applicable':False}
    from powerpro.controllers.checkin_overtime import _settings
    from powerpro.payroll_rules.manual_overtime import verification_roles
    settings=_settings()
    can=bool((cint(settings.get('enable_checkin_overtime_reconciliation')) or cint(settings.get('enable_overtime_evidence_monitor')))
        and frappe.has_permission(source_type,'write',doc=doc)
        and verification_roles(settings.get('overtime_manual_verification_roles')).intersection(frappe.get_roles())
        and (source_type!=RETRO or doc.approver==frappe.session.user))
    saved,revision=effective_snapshot(doc)
    observation_window=physical_input(saved).get('observation_window')
    if not observation_window:
        first=next((r for r in (saved.get('input') or {}).get('contexts',[]) if r.get('date')==str(doc.work_date)),{})
        observation_window=dict(start=str(min(get_datetime(doc.authorization_start),get_datetime(first.get('shift_start') or doc.authorization_start))),
            end=str(max(get_datetime(doc.authorization_end),get_datetime(first.get('shift_end') or doc.authorization_end))))
    return {'applicable':True,'can_review':can,'manual_review_allowed':bool(can and cint(settings.get('enable_manual_overtime_verification'))),
        'revision':revision.name if revision else None,'observation_window':observation_window}
