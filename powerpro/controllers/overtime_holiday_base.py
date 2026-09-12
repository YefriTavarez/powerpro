"""Explicit, source-bound declaration of holiday base already covered by salary.

Uses the existing immutable reconciliation audit; never infers coverage from
monthly salary, changes checkins, approves work, or creates earnings.
"""
from decimal import Decimal, InvalidOperation
import frappe
from frappe import _
from frappe.utils import cint, now_datetime
from powerpro.controllers.overtime_source import AUTH, RETRO, links, evidence_enabled

APPLIED = 'Holiday Salary Base Declared'
MISSING = 'Declare qué horas de feriado ya tienen su base cubierta por el sueldo, incluso si son cero.'


def latest(doc, *, for_update=False):
    from powerpro.controllers.overtime import _reconciliation_rows
    if not doc.name:
        return None
    rows = _reconciliation_rows('Overtime Reconciliation Run', for_update=for_update,
        filters={**links(doc), 'result_status': APPLIED},
        fields=['name', 'evidence'], order_by='history_sequence desc, creation desc, name desc', limit=1)
    if not rows:
        return None
    return {**frappe.parse_json(rows[0].evidence), 'audit': rows[0].name}


def basis_hash(data):
    from powerpro.controllers.checkin_overtime import _evidence_hash
    return _evidence_hash({k: v for k, v in data.items() if k != 'holiday_base_coverage'})


def validate_hours(value, total):
    try:
        hours = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError('Indique un número válido de horas con base cubierta.')
    if not hours.is_finite() or hours < 0 or hours > Decimal(str(total)):
        raise ValueError('Las horas con base cubierta deben estar entre cero y las horas de feriado verificadas.')
    return float(hours)


def apply_to_result(result):
    data = result['input']
    calculation = result.get('calculation') or {}
    total = calculation.get('holiday_100_hours', 0)
    if not total:
        return
    coverage = data.get('holiday_base_coverage')
    if not coverage:
        result['settlement_blockers'].append(MISSING)
        return
    if coverage.get('basis_hash') != basis_hash(data):
        result['settlement_blockers'].append('Cambió la jornada, tarifa o política; revise la cobertura salarial del feriado.')
        return
    try:
        covered = validate_hours(coverage.get('covered_hours'), total)
    except ValueError as exc:
        result['settlement_blockers'].append(str(exc))
        return
    calculation['holiday_base_covered_hours'] = covered
    result['holiday_base_coverage'] = coverage


def _access(doc):
    from powerpro.controllers.checkin_overtime import _access as access, _settings, FINAL
    if doc.doctype not in {AUTH, RETRO}:
        frappe.throw(_('Origen no admitido.'))
    access(doc)
    if not evidence_enabled(doc) or not cint(_settings().get('enable_checkin_overtime_reconciliation')):
        frappe.throw(_('Habilite conciliación por marcaciones para declarar la cobertura.'))
    if doc.docstatus == 2 or doc.get('settlement_status') in FINAL:
        frappe.throw(_('Resuelva la liquidación existente antes de cambiar la cobertura salarial.'))
    if doc.planned_settlement != 'Cash':
        frappe.throw(_('Esta declaración corresponde a una liquidación en efectivo.'))
    if doc.doctype == AUTH and (doc.docstatus != 1 or doc.status != 'Approved'):
        frappe.throw(_('La autorización debe estar aprobada.'))
    if doc.doctype == RETRO:
        doc.check_permission('submit')
        if doc.approver != frappe.session.user:
            frappe.throw(_('Solo el aprobador asignado puede declarar esta cobertura.'), frappe.PermissionError)


def _preview(doc, covered_hours, reference, *, for_update=False):
    from powerpro.controllers import checkin_overtime as evidence
    from powerpro.payroll_rules.overtime_cash_settlement import calculate_cash_settlement
    from powerpro.payroll_rules.overtime_pay_policy import rates
    if not isinstance(reference, str) or not 1 <= len(reference.strip()) <= 2000:
        frappe.throw(_('Indique la referencia salarial que respalda las horas cubiertas o su ausencia.'))
    result = evidence.build_result(doc, for_update=for_update)
    if not result.get('snapshot') or result['state'] not in {'Verified', 'Needs Review'}:
        frappe.throw(_('Primero complete la evidencia de las horas trabajadas.'))
    total = result['calculation'].get('holiday_100_hours', 0)
    if total <= 0:
        frappe.throw(_('La conciliación no contiene horas de feriado.'))
    hours = validate_hours(covered_hours, total)
    data = result['input']
    declaration = {'covered_hours': hours, 'holiday_hours': total,
        'reference': reference.strip(), 'basis_hash': basis_hash(data)}
    previous = data.get('holiday_base_coverage')
    token = evidence._evidence_hash({**links(doc), 'declaration': declaration,
        'previous': previous, 'settlement_status': doc.get('settlement_status'),
        'approver': doc.get('approver'), 'employee': doc.employee})
    estimate = None
    if data.get('pay_policy') and data.get('rate_basis'):
        from powerpro.payroll_rules.overtime_combined_day import cash_kwargs
        try:
            combined=cash_kwargs(data['pay_policy'],result['calculation'])
        except ValueError:
            combined=None  # Coverage can be documented while the joint rule awaits review.
        if combined is not None:
            estimate = calculate_cash_settlement(hourly_rate=data['rate_basis']['hourly_rate'],
                **{k: result['calculation'].get(k, 0) for k in
                   ['regular_35_hours', 'regular_100_hours', 'holiday_100_hours', 'night_hours', 'weekly_rest_hours']},
                holiday_base_covered_hours=hours, **rates(data['pay_policy']), **combined)
    return {'token': token, 'declaration': declaration, 'estimate': estimate,
        'previous': previous, 'sequence': (previous or {}).get('sequence', 0) + 1,
        'issues': result.get('issues', []), 'settlement_blockers': result['settlement_blockers']}


@frappe.whitelist()
def preview(source_type, source_name, covered_hours, reference):
    if source_type not in {AUTH, RETRO}:
        frappe.throw(_('Origen no admitido.'))
    doc = frappe.get_doc(source_type, source_name)
    _access(doc)
    return _preview(doc, covered_hours, reference)


@frappe.whitelist()
def get_status(source_type, source_name):
    if source_type not in {AUTH, RETRO}:
        frappe.throw(_('Origen no admitido.'))
    doc = frappe.get_doc(source_type, source_name)
    doc.check_permission('read')
    muted = frappe.flags.mute_messages
    frappe.flags.mute_messages = True
    try:
        _access(doc)
    except (frappe.PermissionError, frappe.ValidationError):
        return {'can_declare': False}
    finally:
        frappe.flags.mute_messages = muted
    return {'can_declare': True, 'coverage': latest(doc)}


@frappe.whitelist(methods=['POST'])
def apply(source_type, source_name, covered_hours, reference, token):
    from powerpro.controllers.overtime_rest import _lock_source
    from powerpro.controllers.checkin_overtime import _json
    if source_type not in {AUTH, RETRO}:
        frappe.throw(_('Origen no admitido.'))
    doc, _call = _lock_source(source_name, source_type=source_type, allow_cancelled=True)
    _access(doc)
    existing = frappe.db.get_value('Overtime Reconciliation Run',
        {**links(doc), 'result_status': APPLIED, 'evidence_hash': token}, 'name', for_update=True)
    if existing:
        return {'audit': existing, 'idempotent': True}
    p = _preview(doc, covered_hours, reference, for_update=True)
    if not token or token != p['token']:
        frappe.throw(_('Cambió la evidencia o la declaración; obtenga otra vista previa.'))
    declaration = {**p['declaration'], 'declared_by': frappe.session.user,
        'declared_on': str(now_datetime()), 'sequence': p['sequence'],
        'previous_audit': (p['previous'] or {}).get('audit')}
    run = frappe.new_doc('Overtime Reconciliation Run')
    run.update({**links(doc), 'employee': doc.employee, 'work_date': doc.work_date,
        'result_status': APPLIED, 'history_sequence': p['sequence'], 'evidence_hash': token,
        'evidence': _json(declaration), 'issues': '[]',
        'evaluated_by': frappe.session.user, 'evaluated_on': now_datetime()})
    run.name = frappe.generate_hash(length=16)
    run.db_insert()
    return {'audit': run.name, 'idempotent': False}
