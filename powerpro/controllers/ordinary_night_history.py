"""Append-only physical reviews of cancelled ordinary-night settlements.

No earnings, current salary rate or financial policy enter this evidence path.
The original source and its documented extension identities remain immutable.
"""
from copy import deepcopy
import frappe
from frappe import _
from frappe.utils import cint,get_datetime,getdate,now_datetime
from powerpro.controllers import ordinary_night as night
from powerpro.controllers.checkin_overtime import _evidence_hash,_json,_settings
from powerpro.controllers.overtime import _reconciliation_rows
from powerpro.controllers.overtime_history import APPLIED,_hours

DT=night.DT
RUN='Overtime Reconciliation Run'
PHYSICAL_KEYS=('version','employee','company','work_date','shift','context','extensions','next_windows','rows')


def physical_input(snapshot):
    data=snapshot.get('input') or {}
    result={k:data[k] for k in PHYSICAL_KEYS if k in data}
    declaration=data.get('manual_declaration') or ((data.get('certified_session') or {}).get('review') or {}).get('manual_declaration')
    if declaration:result['manual_declaration']=declaration
    return result


def latest(doc,*,for_update=False):
    rows=_reconciliation_rows(RUN,for_update=for_update,filters={'night_settlement':doc.name,'result_status':APPLIED},
        fields=['name','history_sequence','evidence'],order_by='history_sequence desc,creation desc,name desc',limit=1)
    return rows[0] if rows else None


def effective_snapshot(doc,*,for_update=False):
    revision=latest(doc,for_update=for_update)
    return (frappe.parse_json(revision.evidence)['after'] if revision else frappe.parse_json(doc.evidence_snapshot or '{}')),revision


def historical_extensions(doc,snapshot,*,for_update=False):
    windows=(snapshot.get('input') or {}).get('extensions') or []
    if not isinstance(windows,list) or len(windows)>50:frappe.throw(_('Prolongaciones históricas inválidas.'))
    extensions=[];seen=set()
    for window in windows:
        dt=window.get('source_type') or 'Overtime Authorization';name=window.get('name')
        if dt not in {'Overtime Authorization','Retroactive Overtime Adjustment'} or not name or (dt,name) in seen:
            frappe.throw(_('Referencia histórica de prolongación inválida.'))
        seen.add((dt,name))
        ref=frappe.get_doc(dt,name,for_update=for_update);ref.check_permission('read')
        if ref.docstatus not in {1,2} or ref.employee!=doc.employee or getdate(ref.work_date)!=getdate(doc.work_date):
            frappe.throw(_('La prolongación histórica no corresponde al origen cancelado.'))
        extensions.append(frappe._dict(name=ref.name,authorization_start=ref.authorization_start,authorization_end=ref.authorization_end,
            status=ref.status,docstatus=ref.docstatus,shift_type=ref.shift_type,**({'source_type':dt} if dt!='Overtime Authorization' else {})))
    return extensions


def evaluate_physical(doc,company,rows,shift,context,windows,next_windows,declaration):
    from powerpro.payroll_rules.ordinary_night import evaluate_night_work,VERSION
    from powerpro.payroll_rules.overtime_manual_session import validate_manual_intervals
    certified=None
    if declaration is not None:
        start=min([get_datetime(context['shift_start'])]+[get_datetime(w['start']) for w in windows])
        end=max([get_datetime(context['shift_end'])]+[get_datetime(w['end']) for w in windows])
        # Validate the complete declaration through the same bounded interval
        # contract used by HR, including reference, pauses and elapsed window.
        worked=validate_manual_intervals(declaration,start,end,night.now_datetime())
        certified=[{'start':a.isoformat(),'end':b.isoformat()} for a,b in worked]
    result=evaluate_night_work(rows=[dict(r) for r in rows],shift=shift,context=context,extensions=windows,
        next_windows=next_windows,now=night.now_datetime(),basis='Clock overlap',certified_intervals=certified)
    data=dict(version=VERSION,employee=doc.employee,company=company,work_date=str(getdate(doc.work_date)),
        shift=shift,context=context,extensions=windows,next_windows=next_windows,rows=[dict(r) for r in rows])
    if declaration is not None:
        data['manual_declaration']=deepcopy(declaration);result['manual_declaration']=deepcopy(declaration)
        result['certified_sessions']=[{'shift':shift['name'],'start':str(context['shift_start']),'end':str(context['shift_end'])}]
    result.update(input=data,input_hash=_evidence_hash(data),historical_only=True)
    return result


def evaluate(doc,saved,*,for_update=False,declaration=None):
    return night.build_preview(doc,for_update=for_update,historical_snapshot=saved,historical_declaration=declaration)


def compare(doc,*,for_update=False):
    saved,revision=effective_snapshot(doc,for_update=for_update)
    current=evaluate(doc,saved,for_update=for_update,declaration=physical_input(saved).get('manual_declaration'))
    same=bool(current['state']=='Verified' and current.get('worked_intervals')
        and _evidence_hash(physical_input(saved))==current['input_hash']
        and _evidence_hash(saved.get('source_checkins'))==_evidence_hash(current.get('source_checkins'))
        and _evidence_hash(saved.get('worked_intervals'))==_evidence_hash(current.get('worked_intervals')))
    return dict(saved=saved,current=current,revision=revision,matches=same)


def _access(doc):
    doc.check_permission('read');doc.check_permission('write');night.check_role()
    frappe.get_doc('Employee',doc.employee).check_permission('read')
    if doc.doctype!=DT or doc.docstatus!=2 or not doc.evidence_snapshot:
        frappe.throw(_('Seleccione una liquidación nocturna cancelada con evidencia conservada.'))
    settings=_settings()
    if not (cint(settings.get('enable_checkin_overtime_reconciliation')) or cint(settings.get('enable_overtime_evidence_monitor'))):
        frappe.throw(_('Habilite la revisión de marcaciones o su seguimiento para corregir el historial.'))
    if not frappe.has_permission(RUN,'read'):frappe.throw(_('Necesita acceso a la auditoría de conciliación.'),frappe.PermissionError)


def _references(saved,revision=None):
    refs=[('Employee Checkin',r['name']) for r in saved.get('source_checkins',[])]
    refs.extend((r.get('source_type') or 'Overtime Authorization',r['name']) for r in (saved.get('input') or {}).get('extensions',[]))
    if revision:refs.append((RUN,revision.name))
    for dt,name in refs:
        if not frappe.has_permission(dt,'read',doc=name):frappe.throw(_('Falta acceso a una referencia de evidencia histórica.'),frappe.PermissionError)


def _preview(doc,reason,declaration=None,*,for_update=False):
    from powerpro.controllers.overtime_cash_settlement import _get_linked_additional_salaries
    if not isinstance(reason,str) or not 1<=len(reason.strip())<=2000:frappe.throw(_('Documente el motivo de la revisión histórica.'))
    if isinstance(declaration,str):declaration=frappe.parse_json(declaration)
    if declaration is not None and not cint(_settings().get('enable_manual_overtime_verification')):
        frappe.throw(_('La declaración manual está desactivada.'))
    if _get_linked_additional_salaries(doc,docstatus=1,for_update=for_update):
        frappe.throw(_('Revierta primero los salarios adicionales del origen cancelado.'))
    saved,revision=effective_snapshot(doc,for_update=for_update)
    _references(saved,revision)
    try:current=evaluate(doc,saved,for_update=for_update,declaration=declaration)
    except ValueError as exc:frappe.throw(str(exc))
    _references(current)
    if current['state']!='Verified' or not current.get('worked_intervals'):
        frappe.throw(_('Complete la evidencia física y resuelva las marcaciones faltantes o ambiguas antes de aceptar.'))
    if (_evidence_hash(physical_input(saved))==current['input_hash']
        and _evidence_hash(saved.get('worked_intervals'))==_evidence_hash(current['worked_intervals'])):
        frappe.throw(_('La evidencia física no cambió; no hace falta otra revisión histórica.'))
    # This adapter only feeds diagnostic incidents, never weekly financial
    # calculations or replacement settlements; those still require fresh proof.
    stable=dict(night_settlement=doc.name,reason=reason.strip(),before=_evidence_hash(saved),
        revision=revision.name if revision else None,after=current['input_hash'],worked=current['worked_intervals'])
    return dict(token=_evidence_hash(stable),saved=saved,current=current,revision=revision,
        sequence=cint(revision.history_sequence) if revision else 0,reason=reason.strip())


@frappe.whitelist()
def preview_review(name,reason,manual_declaration=None):
    doc=frappe.get_doc(DT,name);_access(doc)
    p=_preview(doc,reason,manual_declaration)
    return dict(token=p['token'],night_settlement=doc.name,historical_only=True,settlement_ready=False,
        worked_hours_before=_hours(p['saved']),worked_hours_after=_hours(p['current']),
        worked_intervals=p['current']['worked_intervals'],source_checkins=p['current']['source_checkins'],
        revision=p['revision'].name if p['revision'] else None,
        note=_('Solo se revisa el trabajo histórico; la liquidación permanece cancelada.'))


@frappe.whitelist(methods=['POST'])
def apply_review(name,reason,token,manual_declaration=None):
    from powerpro.controllers.overtime_evidence_monitor import _source
    doc=_source(DT,name);_access(doc)
    existing=_reconciliation_rows(RUN,for_update=True,filters={'night_settlement':name,'result_status':APPLIED,'evidence_hash':token},pluck='name',limit=1)
    if existing:
        _references({},frappe._dict(name=existing[0]))
        return dict(status='Applied',audit=existing[0],idempotent=True)
    p=_preview(doc,reason,manual_declaration,for_update=True)
    if not token or token!=p['token']:frappe.throw(_('La evidencia histórica cambió; obtenga una vista previa nueva.'))
    after=deepcopy(p['current']);after['review']=dict(reason=p['reason'],reviewed_by=frappe.session.user,
        reviewed_on=str(now_datetime()),request_token=token,input_hash=after['input_hash'])
    record=frappe.new_doc(RUN)
    record.update(dict(night_settlement=doc.name,employee=doc.employee,work_date=doc.work_date,result_status=APPLIED,
        history_sequence=p['sequence']+1,evidence_hash=token,evaluated_by=frappe.session.user,evaluated_on=now_datetime(),
        evidence=_json(dict(before=p['saved'],after=after,previous_revision=p['revision'].name if p['revision'] else None,historical_only=True)),
        issues=_json(after['issues'])))
    record.name=frappe.generate_hash(length=16);record.db_insert()
    return dict(status='Applied',audit=record.name,history_sequence=record.history_sequence,historical_only=True)


@frappe.whitelist()
def get_status(name):
    from powerpro.payroll_rules.manual_overtime import verification_roles
    doc=frappe.get_doc(DT,name);doc.check_permission('read')
    frappe.get_doc('Employee',doc.employee).check_permission('read')
    if doc.docstatus!=2 or not doc.evidence_snapshot:return {'applicable':False}
    settings=_settings()
    can=bool((cint(settings.get('enable_checkin_overtime_reconciliation')) or cint(settings.get('enable_overtime_evidence_monitor')))
        and frappe.has_permission(DT,'write',doc=doc) and frappe.has_permission(RUN,'read')
        and verification_roles(settings.get('overtime_manual_verification_roles')).intersection(frappe.get_roles()))
    saved,revision=effective_snapshot(doc);_references(saved,revision)
    result=dict(applicable=True,can_review=can,historical_only=True,settlement_status=doc.settlement_status,
        manual_review_allowed=bool(can and cint(settings.get('enable_manual_overtime_verification'))),
        revision=revision.name if revision else None)
    try:
        comparison=compare(doc);_references(comparison['current'])
        return {**result,'state':'Verified' if comparison['matches'] else 'Needs Review','issues':comparison['current']['issues']}
    except frappe.PermissionError:raise
    except (frappe.ValidationError,ValueError):
        return {**result,'state':'Needs Review','issues':[{'code':'historical_evidence_requires_review'}]}
