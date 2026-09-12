"""DEV-only native documentary approval/election/cash trial; default rollback.

Consumes a private hashed plan. Retains unresolved combined-day rules and real
weekly incompleteness. Does not create slips, change punches or run payroll.
"""
import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import frappe
from import_overtime_checkin_sample import SITE, canonical, settings

RETRO = 'Retroactive Overtime Adjustment'
POLICY = 'Overtime Pay Policy'
ELECTION = 'Overtime Settlement Election'
RUN = 'Overtime Reconciliation Run'


def apply_plan(plan):
    from powerpro.controllers import retroactive_evidence, retroactive_draft_review, overtime_rest
    from powerpro.controllers.overtime_cash_settlement import create_cash_settlement
    if frappe.local.site != SITE or not frappe.conf.developer_mode or frappe.session.user != 'Administrator':
        raise frappe.PermissionError('DEV Administrator only')
    if plan['site'] != SITE or len(plan['cases']) != 2:
        raise ValueError('Exactly two documented DEV weekend cases required')
    if frappe.db.get_single_value('System Settings', 'enable_scheduler'):
        raise ValueError('Keep DEV scheduler disabled')
    policy_values = plan['policy']
    if (policy_values['holiday_weekly_rest_mode'] != 'Require review'
            or policy_values['enable_compensatory'] or not policy_values['weekly_rest_cash']):
        raise ValueError('Only confirmed cash configuration; combined-day policy remains under review')
    matches = frappe.get_all(POLICY, pluck='name')
    if matches:
        if len(matches) != 1: raise ValueError('Review other policies before running this sample')
        policy = frappe.get_doc(POLICY, matches[0])
        if any(str(policy.get(k)) != str(v) for k, v in policy_values.items()):
            raise ValueError('Existing policy differs from scoped plan')
        if policy.docstatus != 1: raise ValueError('Existing policy is not approved')
    else:
        policy = frappe.get_doc({'doctype': POLICY, **policy_values})
        policy.insert(); policy.submit()
    outputs = []
    for case in plan['cases']:
        doc = frappe.get_doc(RETRO, case['adjustment'])
        if (doc.employee != plan['employee'] or doc.company != policy.company or doc.approver != frappe.session.user
                or doc.planned_settlement != 'Cash' or doc.docstatus not in (0, 1)):
            raise ValueError('Source identity/state differs')
        comment = frappe.get_doc('Comment', case['choice_comment'])
        if (comment.reference_doctype != RETRO or comment.reference_name != doc.name
                or comment.published or '«Efectivo»' not in comment.content):
            raise ValueError('Missing private reference to the confirmed cash choice')
        audit = retroactive_draft_review.latest(doc)
        if not audit: raise ValueError('Existing documentary review required')
        saved = frappe.parse_json(audit.evidence)['after']
        declaration = saved['review']['manual_declaration']
        if declaration != case['declaration']:
            raise ValueError('Do not change the accepted documentary declaration')
        if doc.docstatus == 0:
            preview = retroactive_draft_review.preview_review(doc.name, saved['review']['reason'], manual_declaration=declaration)
            if abs(preview['after']['verified_hours'] - case['expected_hours']) > .0001:
                raise ValueError('Reviewed hours changed')
            retroactive_draft_review.apply_review(doc.name, saved['review']['reason'], preview['token'], manual_declaration=declaration)
            doc.reload(); doc.submit(); doc.reload()
        if doc.evidence_status != 'Verified' or abs(doc.verified_hours-case['expected_hours']) > .0001:
            raise ValueError('Source is not verified for the expected hours')
        election = overtime_rest.get_election(doc)
        if not election:
            election = frappe.get_doc({'doctype': ELECTION, 'retroactive_adjustment': doc.name,
                'choice': 'Cash', 'employee_reference': 'Usuario confirmó Efectivo para este piloto DEV; referencia a nota interna ' + comment.name,
                'settlement_payroll_date': doc.settlement_payroll_date})
            election.insert(); overtime_rest.approve_election(election.name); election.reload(); doc.reload()
        if election.choice != 'Cash' or election.policy != policy.name:
            raise ValueError('Existing election differs')
        reconciliation = retroactive_evidence.reconcile(doc)
        if reconciliation['weekly_evidence_complete']:
            raise AssertionError('This trial must preserve the unresolved weekly evidence')
        if case['settle']:
            if doc.day_classification != 'Weekly Rest' or not reconciliation['settlement_ready']:
                raise ValueError('Only independently ready weekly-rest cash may be created')
            if doc.settlement_status == 'Pending':
                create_cash_settlement(doc.name); doc.reload()
            if doc.settlement_status != 'Created' or abs(doc.settlement_amount-case['expected_amount']) > .005:
                raise AssertionError('Unexpected cash calculation')
            refs = frappe.parse_json(doc.settlement_references)
            salaries = [frappe.get_doc('Additional Salary', n) for n in refs]
            if not salaries or any(s.docstatus != 1 or s.employee != doc.employee or s.ref_docname != doc.name for s in salaries):
                raise AssertionError('Missing native Additional Salary references')
            if abs(sum(s.amount for s in salaries)-doc.settlement_amount) > .005:
                raise AssertionError('Additional salaries differ from settlement')
            before_retry = frappe.db.count('Additional Salary')
            try: create_cash_settlement(doc.name)
            except frappe.ValidationError: pass
            else: raise AssertionError('Duplicate settlement was not rejected')
            if frappe.db.count('Additional Salary') != before_retry: raise AssertionError('Retry created money')
        else:
            if doc.settlement_status != 'Pending' or doc.settlement_references or reconciliation['settlement_ready']:
                raise AssertionError('Unresolved combined day must not create money')
        outputs.append({'adjustment': doc.name, 'docstatus': doc.docstatus, 'verified_hours': doc.verified_hours,
            'election': election.name, 'choice': election.choice, 'settlement_status': doc.settlement_status,
            'amount': doc.settlement_amount, 'references': frappe.parse_json(doc.settlement_references or '[]'),
            'weekly_evidence_complete': reconciliation['weekly_evidence_complete'],
            'blockers': reconciliation['_evidence']['settlement_blockers']})
    return {'policy': policy.name, 'cases': outputs}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('plan', type=Path); p.add_argument('--sha256', required=True); p.add_argument('--apply', action='store_true')
    args = p.parse_args(); raw = args.plan.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.sha256: raise ValueError('Plan changed')
    plan = json.loads(raw)
    frappe.init(site=SITE); frappe.connect(); frappe.set_user('Administrator')
    protected = ['Employee Checkin','Employee','Attendance','Salary Slip','Overtime Authorization',
                 'Leave Allocation','Leave Application','Email Queue','Overtime Compensatory Credit']
    counts = {dt: frappe.db.count(dt) for dt in protected}
    mutable = [POLICY, RETRO, ELECTION, RUN, 'Additional Salary']
    originals = {dt: {r.name: canonical(frappe.get_doc(dt, r.name).as_dict()) for r in frappe.get_all(dt)} for dt in mutable}
    before_settings = settings()
    def forbidden(*a, **kw): raise AssertionError('Outbound effect attempted')
    try:
        with patch.object(frappe, 'sendmail', forbidden), patch.object(frappe, 'enqueue', forbidden):
            result = apply_plan(plan)
            repeat_counts = {dt: frappe.db.count(dt) for dt in mutable}
            apply_plan(plan)
            if repeat_counts != {dt: frappe.db.count(dt) for dt in mutable}: raise AssertionError('Retry changed counts')
            if counts != {dt: frappe.db.count(dt) for dt in protected} or before_settings != settings():
                raise AssertionError('Protected counts/settings changed')
            allowed = {c['adjustment'] for c in plan['cases']}
            for dt, rows in originals.items():
                for name, value in rows.items():
                    if dt == RETRO and name in allowed: continue
                    if canonical(frappe.get_doc(dt, name).as_dict()) != value:
                        raise AssertionError('Unrelated document changed: ' + dt)
            if args.apply:
                frappe.db.commit(); apply_plan(plan)
                result.update(committed=True, readback_verified=True)
            else:
                frappe.db.rollback()
                for dt, rows in originals.items():
                    if rows != {r.name: canonical(frappe.get_doc(dt,r.name).as_dict()) for r in frappe.get_all(dt)}:
                        raise AssertionError('Rollback failed: ' + dt)
                result.update(committed=False, rollback_verified=True)
            result.update(protected_counts=counts, idempotence_verified=True)
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    finally:
        frappe.db.rollback(); frappe.destroy()


if __name__ == '__main__': main()
