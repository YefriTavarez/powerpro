"""Audited alternative evidence before a historical adjustment is approved."""
from copy import deepcopy
import hashlib
import frappe
from frappe import _
from frappe.utils import cint,now_datetime
from powerpro.controllers.overtime_source import RETRO
from powerpro.controllers.overtime import _reconciliation_rows

APPLIED='Draft Work Evidence Reviewed'


def latest(doc,*,for_update=False):
    rows=_reconciliation_rows('Overtime Reconciliation Run',for_update=for_update,
        filters={'retroactive_adjustment':doc.name,'result_status':APPLIED},
        fields=['name','history_sequence','evidence','evaluated_by','employee'],
        order_by='history_sequence desc, creation desc, name desc',limit=1)
    return rows[0] if rows else None


def _access(doc):
    from powerpro.controllers.checkin_overtime import _access as access,_settings
    from powerpro.controllers.retroactive_evidence import enabled
    access(doc);doc.check_permission('submit')
    if doc.docstatus!=0 or not enabled(doc):frappe.throw(_('La declaración inicial requiere un ajuste en borrador con conciliación por marcaciones.'))
    if doc.approver!=frappe.session.user:frappe.throw(_('Solo el aprobador asignado puede aceptar esta declaración.'),frappe.PermissionError)
    settings=_settings()
    if not cint(settings.get('enable_checkin_overtime_reconciliation')) or not cint(settings.get('enable_manual_overtime_verification')):
        frappe.throw(_('Habilite conciliación y verificación manual para aceptar la declaración.'))
    doc._validate_feature_flag();doc._validate_window()


def _preview(doc,reason,declaration,*,for_update=False):
    from powerpro.controllers.checkin_overtime_review import _preview as preview
    from powerpro.controllers.checkin_overtime import _json
    if not declaration:frappe.throw(_('Declare la jornada completa y su referencia documental.'))
    try:result=preview(doc,reason,for_update=for_update,manual_declaration=declaration)
    except ValueError as exc:frappe.throw(str(exc))
    previous=latest(doc,for_update=for_update)
    result['token']=hashlib.sha256(_json({'review':result['token'],'previous':previous.name if previous else None,
        'modified':str(doc.modified),'approver':doc.approver}).encode()).hexdigest()
    result['sequence']=cint(previous.history_sequence) if previous else 0
    result['previous']=previous.name if previous else None
    return result


@frappe.whitelist()
def preview_review(authorization,reason,manual_declaration=None,source_type=RETRO):
    if source_type!=RETRO:frappe.throw(_('La declaración inicial solo corresponde a ajustes retroactivos.'))
    doc=frappe.get_doc(RETRO,authorization);_access(doc)
    p=_preview(doc,reason,manual_declaration)
    from powerpro.payroll_rules.overtime_pay_policy import review_summary
    return {'token':p['token'],'reason':p['reason'],'before':p['before'].get('snapshot',{}),'after':p['after']['snapshot'],
        'financial_before':p['financial_before'],'proposed_amount':p['proposed_amount'],'dependencies':p['dependencies'],
        'settlement_blockers':p['after']['settlement_blockers'],'draft_only':True,
        'rules_summary':review_summary(p['after']),
        'manual_declaration':p['after']['manual_declaration'],'checkin_comparison':p['after'].get('checkin_comparison')}


@frappe.whitelist(methods=['POST'])
def apply_review(authorization,reason,token,manual_declaration=None,source_type=RETRO):
    if source_type!=RETRO:frappe.throw(_('La declaración inicial solo corresponde a ajustes retroactivos.'))
    from powerpro.controllers.overtime_rest import _lock_source
    from powerpro.controllers.checkin_overtime import _json
    doc,_call=_lock_source(authorization,allow_cancelled=True,source_type=RETRO);_access(doc)
    existing=_reconciliation_rows('Overtime Reconciliation Run',for_update=True,
        filters={'retroactive_adjustment':doc.name,'result_status':APPLIED,'evidence_hash':token},pluck='name',limit=1)
    if existing:return {'status':'Applied','audit':existing[0],'idempotent':True}
    p=_preview(doc,reason,manual_declaration,for_update=True)
    if not token or p['token']!=token:frappe.throw(_('La evidencia o el borrador cambió; obtenga una vista previa nueva.'))
    if any(r['blocks_reversal'] for r in p['dependencies']):
        frappe.throw(_('Resuelva primero las liquidaciones posteriores que dependen de esta jornada.'))
    after=deepcopy(p['after'])
    after['review'].update(reviewed_by=frappe.session.user,reviewed_on=str(now_datetime()),request_token=token,
        manual_declaration=after['manual_declaration'],initial_draft=True)
    record=frappe.new_doc('Overtime Reconciliation Run')
    record.update({'retroactive_adjustment':doc.name,'employee':doc.employee,'work_date':doc.work_date,'result_status':APPLIED,
        'history_sequence':p['sequence']+1,'evidence_hash':token,'evaluated_by':frappe.session.user,'evaluated_on':now_datetime(),
        'evidence':_json({'after':after,'previous_revision':p['previous'],'draft_only':True}), 'issues':_json(after['issues'])})
    record.name=frappe.generate_hash(length=16);record.db_insert()
    return {'status':'Applied','audit':record.name,'draft_only':True}


def reconcile_draft(doc,*,for_update=False):
    """Use only a service-owned audit, never a client-supplied draft snapshot."""
    from powerpro.controllers.checkin_overtime import build_result,_settings,_json
    if doc.is_new() or frappe.db.get_value(RETRO,doc.name,'docstatus')!=0:return None
    audit=latest(doc,for_update=for_update)
    if not audit:return None
    saved=frappe.parse_json(audit.evidence)['after']
    working=deepcopy(doc);working.evidence_snapshot=_json(saved)
    current=build_result(working,for_update=for_update)
    if (current['input_hash']!=saved['input_hash'] or audit.evaluated_by!=doc.approver or audit.employee!=doc.employee
            or not cint(_settings().get('enable_manual_overtime_verification'))):
        current['state']='Needs Review';current['settlement_ready']=False
        current['issues'].append({'code':'draft_declaration_changed','severity':'review',
            'message':_('La declaración inicial requiere nueva revisión: cambió su evidencia, aprobador o configuración.')})
    return current


@frappe.whitelist()
def get_status(adjustment):
    doc=frappe.get_doc(RETRO,adjustment);doc.check_permission('read')
    from powerpro.controllers.retroactive_evidence import enabled
    if doc.docstatus!=0 or not enabled(doc):return {'can_review':False}
    try:_access(doc)
    except (frappe.PermissionError,frappe.ValidationError):return {'can_review':False}
    audit=latest(doc)
    return {'can_review':True,'audit':audit.name if audit else None}
