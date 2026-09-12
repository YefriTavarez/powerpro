"""Historical exceptions using the same evidenced calendar/week/policy engine."""
import frappe
from frappe import _
from frappe.utils import cint,flt,getdate,get_datetime

DT='Retroactive Overtime Adjustment'
ENGINE='Verified Checkins'


def enabled(doc):
    return doc.doctype==DT and doc.get('reconciliation_engine')==ENGINE


def reconcile(doc,*,for_update=False):
    from powerpro.controllers.checkin_overtime import build_result
    return as_reconciliation(doc,build_result(doc,for_update=for_update))


def as_reconciliation(doc,evidence):
    from powerpro.payroll_rules.overtime_pay_policy import rates
    calculation=dict(evidence.get('calculation') or {})
    policy=evidence.get('input',{}).get('pay_policy')
    warnings=[i.get('message') or i['code'] for i in evidence.get('issues',[]) if i.get('severity')!='information']
    warnings.extend(evidence.get('settlement_blockers',[]))
    for issue in evidence.get('weekly_evidence',{}).get('issues',[]):
        if issue.get('authorization'):
            warnings.append(_('Revise la evidencia histórica de {0}: {1}.').format(
                issue.get('source_type') or 'Overtime Authorization',issue['authorization']))
    calculation.update(classification=calculation.get('classification') or doc.day_classification,
        source_checkins=evidence.get('source_checkins',[]),warnings=warnings,
        pay_policy=policy,rate_basis=evidence.get('input',{}).get('rate_basis'),rates=rates(policy) if policy else {},
        settlement_election=evidence.get('settlement_election'),evidence_state=evidence['state'],
        settlement_ready=evidence.get('settlement_ready',False),_evidence=evidence)
    for name in ['verified_hours','regular_35_hours','regular_100_hours','holiday_100_hours','weekly_rest_hours','night_hours']:
        calculation.setdefault(name,0)
    from powerpro.controllers.checkin_overtime import _json
    return frappe.parse_json(_json(calculation))


def prepare_snapshot(doc,result):
    from powerpro.controllers.checkin_overtime import _settings,_json
    settings=_settings()
    if not cint(settings.get('enable_checkin_overtime_reconciliation')):
        frappe.throw(_('El motor de conciliación por marcaciones está desactivado.'))
    if not settings.checkin_overtime_effective_from or getdate(doc.work_date)<getdate(settings.checkin_overtime_effective_from):
        frappe.throw(_('La fecha efectiva del motor debe cubrir el ajuste retroactivo.'))
    evidence=result['_evidence']
    if evidence['state']!='Verified' or not evidence.get('snapshot') or flt(evidence['snapshot'].get('verified_hours'))<=0:
        frappe.throw(_('Complete y revise la evidencia de la jornada antes de aprobar el ajuste: {0}.').format(', '.join(result['warnings'])))
    doc.actual_start=evidence['snapshot']['actual_start'];doc.actual_end=evidence['snapshot']['actual_end']
    doc.reconciliation_source='Employee Checkin';doc.evidence_status='Verified'
    doc.evidence_snapshot=_json(evidence);doc.evidence_settlement_ready=cint(evidence['settlement_ready'])


def validate_fresh(doc,*,payroll=False):
    from powerpro.controllers.checkin_overtime import _evidence_hash,_settings
    if not enabled(doc):return None
    if doc.docstatus!=1 or doc.status!='Approved':
        frappe.throw(_('El ajuste retroactivo debe permanecer aprobado.'))
    if not payroll and not cint(_settings().get('enable_checkin_overtime_reconciliation')):
        frappe.throw(_('La liquidación por marcaciones está desactivada.'))
    saved=frappe.parse_json(doc.evidence_snapshot or '{}')
    current=reconcile(doc,for_update=True)
    evidence=current['_evidence']
    if (not saved.get('input_hash') or saved['input_hash']!=evidence['input_hash']
            or evidence['state']!='Verified' or not evidence['settlement_ready']
            or _evidence_hash(saved.get('snapshot'))!=_evidence_hash(evidence.get('snapshot'))):
        frappe.throw(_('La evidencia histórica, la semana o la política cambió o requiere revisión. Revise el ajuste antes de liquidar o enviar nómina.')+' '+ ' '.join(current['warnings']))
    for name in ['verified_hours','regular_35_hours','regular_100_hours','holiday_100_hours','weekly_rest_hours','night_hours']:
        if abs(flt(doc.get(name))-flt(saved['snapshot'].get(name)))>.00005:
            frappe.throw(_('Las horas del ajuste no coinciden con su evidencia guardada.'))
    for name in ['actual_start','actual_end']:
        if not doc.get(name) or get_datetime(doc.get(name))!=get_datetime(saved['snapshot'].get(name)):
            frappe.throw(_('El horario real del ajuste no coincide con su evidencia guardada.'))
    return current
