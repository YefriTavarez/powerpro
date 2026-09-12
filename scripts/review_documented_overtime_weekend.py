"""Apply a user-authorized weekend assumption through the native draft review.

Explicit DEV only; default rolls back. Persists audited manual evidence, never
submits adjustments or manufactures punches, pay, employee elections or policy.
The private hashed plan must retain that full intervals are an assumption.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import frappe
from frappe.utils import get_datetime, getdate
from import_overtime_checkin_sample import SITE, PROTECTED, canonical, settings

CONFIG_FIELDS = {'enable_checkin_overtime_reconciliation', 'checkin_overtime_effective_from'}
RUN = 'Overtime Reconciliation Run'
RETRO = 'Retroactive Overtime Adjustment'


def review(plan):
    from powerpro.controllers import retroactive_draft_review as service
    from powerpro.controllers import retroactive_evidence
    if frappe.local.site != SITE or not frappe.conf.developer_mode or frappe.session.user != 'Administrator':
        raise frappe.PermissionError('Explicit DEV Administrator required')
    if plan['site'] != SITE or len(plan['cases']) != 2 or not plan.get('operator_instruction'):
        raise ValueError('Two scoped cases and operator instruction required')
    if frappe.db.get_single_value('System Settings', 'enable_scheduler'):
        raise ValueError('Keep the scheduler off')
    if frappe.db.exists('Overtime Authorization', {'evidence_enrolled': 1, 'docstatus': 1}):
        raise ValueError('Review existing enrollments before enabling evidence for this sample')
    config = frappe.get_single('DGII Payroll Settings')
    old_config = deepcopy(config.as_dict())
    all_settings = settings()
    if not config.enable_manual_overtime_verification:
        raise ValueError('Manual verification must already be enabled')
    if config.enable_checkin_overtime_reconciliation and str(config.checkin_overtime_effective_from) != plan['effective_from']:
        raise ValueError('Do not replace an existing active effective date')
    counts = {dt: frappe.db.count(dt) for dt in (*PROTECTED, 'Employee', 'Employee Checkin') if dt != RUN}
    old_runs = frappe.db.count(RUN)
    originals = {c['adjustment']: canonical(frappe.get_doc(RETRO, c['adjustment']).as_dict()) for c in plan['cases']}
    punches = canonical(frappe.get_all('Employee Checkin', filters={'employee': plan['employee']}, fields=['*'], order_by='name'))
    config.enable_checkin_overtime_reconciliation = 1
    config.checkin_overtime_effective_from = plan['effective_from']
    if any(str(old_config.get(k)) != str(config.get(k)) for k in CONFIG_FIELDS): config.save()
    cases = []
    for case in plan['cases']:
        doc = frappe.get_doc(RETRO, case['adjustment'])
        declaration = case['declaration']
        assumption = declaration.get('assumption') or {}
        if doc.employee != plan['employee'] or doc.docstatus != 0 or doc.approver != frappe.session.user:
            raise ValueError('Wrong employee, state or assigned reviewer')
        if getdate(doc.work_date).weekday() not in (5, 6) or declaration.get('full_session') is not True:
            raise ValueError('Only explicitly declared full weekend sessions')
        if not assumption.get('not_clock_verified') or assumption.get('break_deduction_hours') != 0:
            raise ValueError('Preserve the user-authorized assumption and zero deduction')
        intervals = declaration['intervals']
        if len(intervals) != 1 or get_datetime(intervals[0]['start']) != get_datetime(doc.authorization_start) or get_datetime(intervals[0]['end']) != get_datetime(doc.authorization_end):
            raise ValueError('Declaration must match the existing documentary window')
        latest = service.latest(doc)
        needs_review = True
        if latest:
            saved = frappe.parse_json(latest.evidence)['after']
            if saved['review'].get('manual_declaration') != declaration or saved['review']['reason'] != plan['reason']:
                raise ValueError('An existing different review requires explicit amendment')
            applied = {'audit': latest.name, 'idempotent': True}
            created = False
            current = retroactive_evidence.reconcile(doc)
            needs_review = current['evidence_state'] != 'Verified'
        if needs_review:
            preview = service.preview_review(doc.name, plan['reason'], manual_declaration=declaration)
            if abs(preview['after']['verified_hours'] - case['expected_hours']) > .0001:
                raise AssertionError('Unexpected reviewed hours')
            applied = service.apply_review(doc.name, plan['reason'], preview['token'], manual_declaration=declaration)
            repeated = service.apply_review(doc.name, plan['reason'], preview['token'], manual_declaration=declaration)
            if not repeated.get('idempotent'): raise AssertionError('Native review did not reuse its audit')
            created = True
        doc.reload()
        if canonical(doc.as_dict()) != originals[doc.name]: raise AssertionError('Draft or financial snapshot changed')
        current = retroactive_evidence.reconcile(doc)
        if current['evidence_state'] != 'Verified' or abs(current['verified_hours'] - case['expected_hours']) > .0001:
            raise AssertionError('Saved manual review is not current')
        audit = frappe.get_doc(RUN, applied['audit'])
        saved = frappe.parse_json(audit.evidence)['after']
        if saved['review']['manual_declaration'] != declaration or saved['review']['reviewed_by'] != 'Administrator':
            raise AssertionError('Audit lost the declaration or reviewer')
        cases.append({'adjustment': doc.name, 'audit': audit.name, 'created': created,
                      'manual_hours': current['verified_hours'], 'docstatus': doc.docstatus,
                      'state': current['evidence_state'], 'settlement_ready': current['settlement_ready'],
                      'settlement_blockers': current['_evidence']['settlement_blockers'],
                      'comparison_state': saved.get('checkin_comparison', {}).get('state'),
                      'assumption_preserved': True})
    new_config = frappe.get_single('DGII Payroll Settings').as_dict()
    allowed = CONFIG_FIELDS | {'modified', 'modified_by'}
    if {k:v for k,v in old_config.items() if k not in allowed} != {k:v for k,v in new_config.items() if k not in allowed}:
        raise AssertionError('Unrelated typed settings changed')
    for dt, previous in all_settings.items():
        if dt != 'DGII Payroll Settings' and previous != settings()[dt]: raise AssertionError('Other settings changed')
    if counts != {dt: frappe.db.count(dt) for dt in counts}: raise AssertionError('Protected counts changed')
    if frappe.db.count(RUN) != old_runs + sum(c['created'] for c in cases): raise AssertionError('Unexpected audit count')
    if punches != canonical(frappe.get_all('Employee Checkin', filters={'employee': plan['employee']}, fields=['*'], order_by='name')):
        raise AssertionError('Checkins changed')
    return {'site': SITE, 'employee': plan['employee'], 'cases': cases, 'counts': counts,
            'settings_before': {k: old_config.get(k) for k in CONFIG_FIELDS},
            'settings_after': {k: new_config.get(k) for k in CONFIG_FIELDS},
            'drafts_unchanged': True, 'checkins_unchanged': True}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('plan', type=Path); p.add_argument('--sha256', required=True); p.add_argument('--apply', action='store_true')
    args = p.parse_args(); raw = args.plan.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.sha256: raise ValueError('Plan changed')
    plan = json.loads(raw)
    frappe.init(site=SITE); frappe.connect(); frappe.set_user('Administrator')
    before = settings(); before_runs = frappe.db.count(RUN)
    def forbidden(*args, **kwargs): raise AssertionError('Outbound action attempted')
    try:
        with patch.object(frappe, 'sendmail', forbidden), patch.object(frappe, 'enqueue', forbidden):
            result = review(plan)
            if any(c['created'] for c in review(plan)['cases']): raise AssertionError('Repeat duplicated audit')
            result['idempotence_verified'] = True
            if args.apply:
                frappe.db.commit()
                if any(c['created'] for c in review(plan)['cases']): raise AssertionError('Postcommit audit missing')
                result.update(committed=True, readback_verified=True)
            else:
                frappe.db.rollback()
                if settings() != before or frappe.db.count(RUN) != before_runs: raise AssertionError('Rollback failed')
                result.update(committed=False, rollback_verified=True)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    finally:
        frappe.db.rollback(); frappe.destroy()


if __name__ == '__main__': main()
