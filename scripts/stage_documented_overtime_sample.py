"""DEV-only native drafts for a hashed, accepted documentary sample.

Requires existing private source attachments, no scheduler or evidence engine.
Updates only two historical settings and one employee's eligibility/approver.
No submit, reconciliation approval, cash, leave, checkin or calendar mutation.
Default rolls back. --apply commits and verifies a duplicate-free readback.
"""
import argparse
import hashlib
import json
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import frappe
from frappe.utils import getdate, get_datetime, nowdate
from import_overtime_checkin_sample import SITE, PROTECTED, canonical, settings

RETRO = 'Retroactive Overtime Adjustment'
SETTING_FIELDS = {'retroactive_overtime_to_date', 'retroactive_overtime_submission_deadline'}
EMPLOYEE_FIELDS = {'overtime_eligible', 'overtime_approver'}


def without_metadata(doc, allowed=()):
    return {k: v for k, v in doc.items() if k not in {*allowed, 'modified', 'modified_by', '_comments'}}


def semantic_settings(snapshot):
    """Native Single.save materializes numeric defaults previously absent in SQL."""
    result = {}
    for dt, values in snapshot.items():
        row = {k: v for k, v in without_metadata(
            values, SETTING_FIELDS if dt == 'DGII Payroll Settings' else ()).items() if v is not None}
        for field in frappe.get_meta(dt).fields:
            if field.fieldtype in {'Check', 'Int', 'Float', 'Currency', 'Percent'}:
                row[field.fieldname] = Decimal(str(row.get(field.fieldname) or 0))
        result[dt] = row
    return result


def validate_plan(plan):
    if plan['site'] != SITE or plan.get('source_accepted') is not True:
        raise ValueError('Explicit DEV and accepted document required')
    if set(plan['target_settings']) != SETTING_FIELDS or set(plan['expected_settings']) != SETTING_FIELDS:
        raise ValueError('Only the historical upper date and deadline may change')
    windows = plan['windows']
    if not 1 <= len(windows) <= 3 or len({w['date'] for w in windows}) != len(windows):
        raise ValueError('One to three distinct work dates required')
    if not getdate(nowdate()) <= getdate(plan['review_deadline']) <= getdate(nowdate()) + timedelta(days=7):
        raise ValueError('Review deadline must be within the next seven days')
    if plan['review_deadline'] != plan['target_settings']['retroactive_overtime_submission_deadline']:
        raise ValueError('Deadline mismatch')
    for w in windows:
        a, b = get_datetime(w['start']), get_datetime(w['end'])
        if w['date'] in plan['excluded_dates'] or a.date() != getdate(w['date']) or b.date() != a.date():
            raise ValueError('Excluded date or invalid day window')
        hours = (b-a).total_seconds()/3600
        if not 0 < hours <= 24 or abs(hours-float(w['maximum_hours'])) > .0001:
            raise ValueError('Invalid documentary window')
    if getdate(plan['target_settings']['retroactive_overtime_to_date']) != max(getdate(w['date']) for w in windows):
        raise ValueError('Historical range must end at the last sample date')


def stage(plan):
    if frappe.local.site != SITE or not frappe.conf.developer_mode or frappe.session.user != 'Administrator':
        raise frappe.PermissionError('DEV Administrator only')
    validate_plan(plan)
    if frappe.db.get_single_value('System Settings', 'enable_scheduler') or frappe.db.get_single_value(
            'DGII Payroll Settings', 'enable_checkin_overtime_reconciliation'):
        raise ValueError('Keep scheduler and evidence automation off while staging drafts')
    employee = frappe.get_doc('Employee', plan['employee'])
    original_employee = employee.as_dict()
    original_settings = settings()
    counts = {dt: frappe.db.count(dt) for dt in (*PROTECTED, 'Employee', 'Employee Checkin') if dt != RETRO}
    old_retros = {r.name: canonical(frappe.get_doc(RETRO, r.name).as_dict()) for r in frappe.get_all(RETRO)}
    punches = canonical(frappe.get_all('Employee Checkin', filters={'employee': employee.name}, fields=['*'], order_by='name'))
    for dt in ('Shift Type', 'Holiday List'):
        if not frappe.db.exists(dt, employee.get('default_shift' if dt == 'Shift Type' else 'holiday_list')):
            raise ValueError('Existing employee shift and calendar required')
    source_files = []
    for row in plan['files']:
        file = frappe.get_doc('File', row['name'])
        content = file.get_content()
        if isinstance(content, str): content = content.encode()
        if file.attached_to_doctype != 'Employee' or file.attached_to_name != employee.name or not file.is_private:
            raise ValueError('Source file must be a private attachment of the selected employee')
        if hashlib.sha256(content).hexdigest() != row['sha256']:
            raise ValueError('Source file changed')
        source_files.append(file)
    config = frappe.get_single('DGII Payroll Settings')
    for key in SETTING_FIELDS:
        if str(config.get(key)) not in {plan['expected_settings'][key], plan['target_settings'][key]}:
            raise ValueError('Historical configuration changed since review')
    if any(str(config.get(k)) != v for k, v in plan['target_settings'].items()):
        config.update(plan['target_settings'])
        config.save()
    if employee.overtime_approver and employee.overtime_approver != plan['approver']:
        raise ValueError('Do not replace an existing different approver')
    if not employee.overtime_eligible or employee.overtime_approver != plan['approver']:
        employee.update({'overtime_eligible': 1, 'overtime_approver': plan['approver']})
        employee.save()
    references = '\n'.join(f.file_url for f in source_files)
    references += '\nPDF original SHA256: ' + plan['source_pdf_sha256']
    drafted = []
    for w in plan['windows']:
        values = {'employee': employee.name, 'work_date': w['date'], 'authorization_start': w['start'],
                  'authorization_end': w['end'], 'maximum_hours': w['maximum_hours'],
                  'reason': plan['reason'], 'exception_justification': plan['exception_justification'],
                  'supporting_reference': references, 'reconciliation_engine': 'Verified Checkins',
                  'planned_settlement': 'Cash', 'settlement_payroll_date': plan['draft_payroll_date']}
        matches = frappe.get_all(RETRO, filters={'employee': employee.name, 'work_date': w['date'], 'docstatus': ['<', 2]}, pluck='name')
        if len(matches) > 1:
            raise ValueError('Multiple active adjustments for the sample day')
        created = not matches
        if matches:
            doc = frappe.get_doc(RETRO, matches[0])
            for key, value in values.items():
                actual = doc.get(key)
                if key == 'maximum_hours':
                    if abs(float(actual)-float(value)) > .0001: raise ValueError('Existing draft differs')
                elif str(actual) != str(value):
                    raise ValueError('Existing draft differs: ' + key)
        else:
            doc = frappe.get_doc({'doctype': RETRO, **values})
            doc.insert()
        if doc.docstatus != 0 or doc.status != 'Draft' or doc.verified_hours or doc.evidence_settlement_ready or doc.settlement_references:
            raise ValueError('Only unverified, unsettled drafts may be staged')
        for file in source_files:
            match = frappe.db.exists('File', {'attached_to_doctype': RETRO, 'attached_to_name': doc.name,
                                              'file_url': file.file_url, 'is_private': 1})
            if not match:
                frappe.get_doc({'doctype': 'File', 'file_name': file.file_name, 'file_url': file.file_url,
                    'is_private': 1, 'attached_to_doctype': RETRO, 'attached_to_name': doc.name}).insert()
        drafted.append({'name': doc.name, 'date': w['date'], 'created': created,
                        'docstatus': doc.docstatus, 'maximum_hours': doc.maximum_hours,
                        'day_classification': doc.day_classification, 'approver': doc.approver})
    after_settings = settings()
    before_filtered = semantic_settings(original_settings)
    after_filtered = semantic_settings(after_settings)
    if before_filtered != after_filtered:
        changed = {dt: [k for k in set(before_filtered[dt]) | set(after_filtered[dt])
                       if before_filtered[dt].get(k) != after_filtered[dt].get(k)]
                   for dt in before_filtered if before_filtered[dt] != after_filtered[dt]}
        raise AssertionError('Unrelated settings changed: ' + canonical(changed))
    if canonical(without_metadata(original_employee, EMPLOYEE_FIELDS)) != canonical(without_metadata(
            frappe.get_doc('Employee', employee.name).as_dict(), EMPLOYEE_FIELDS)):
        raise AssertionError('Unrelated employee fields changed')
    if counts != {dt: frappe.db.count(dt) for dt in counts}:
        raise AssertionError('Protected document counts changed')
    if any(raw != canonical(frappe.get_doc(RETRO, name).as_dict()) for name, raw in old_retros.items()):
        raise AssertionError('Existing adjustment changed')
    if punches != canonical(frappe.get_all('Employee Checkin', filters={'employee': employee.name}, fields=['*'], order_by='name')):
        raise AssertionError('Checkins changed')
    if frappe.db.count(RETRO) != len(old_retros) + sum(d['created'] for d in drafted):
        raise AssertionError('Unexpected adjustment count')
    return {'site': SITE, 'employee': employee.name, 'drafts': drafted,
            'settings_before': {k: original_settings['DGII Payroll Settings'].get(k) for k in SETTING_FIELDS},
            'settings_after': {k: after_settings['DGII Payroll Settings'].get(k) for k in SETTING_FIELDS},
            'employee_before': {k: original_employee.get(k) for k in EMPLOYEE_FIELDS},
            'employee_after': {k: employee.get(k) for k in EMPLOYEE_FIELDS},
            'protected_counts': counts, 'checkins_unchanged': True, 'existing_adjustments_unchanged': True}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('plan', type=Path); p.add_argument('--sha256', required=True); p.add_argument('--apply', action='store_true')
    args = p.parse_args(); raw = args.plan.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.sha256: raise ValueError('Plan hash changed')
    plan = json.loads(raw)
    frappe.init(site=SITE); frappe.connect(); frappe.set_user('Administrator')
    def forbidden(*args, **kwargs): raise AssertionError('Outbound action attempted')
    before_settings = settings()
    before_employee = canonical(frappe.get_doc('Employee', plan['employee']).as_dict())
    try:
        with patch.object(frappe, 'sendmail', forbidden), patch.object(frappe, 'enqueue', forbidden):
            result = stage(plan)
            repeated = stage(plan)
            if any(d['created'] for d in repeated['drafts']): raise AssertionError('Duplicate draft created')
            result['idempotence_verified'] = True
            if args.apply:
                frappe.db.commit()
                readback = stage(plan)
                if any(d['created'] for d in readback['drafts']): raise AssertionError('Readback failed')
                result.update(committed=True, readback_verified=True)
            else:
                frappe.db.rollback()
                if before_settings != settings() or before_employee != canonical(frappe.get_doc('Employee', plan['employee']).as_dict()):
                    raise AssertionError('Rollback did not restore original state')
                if any(d['created'] and frappe.db.exists(RETRO, d['name']) for d in result['drafts']):
                    raise AssertionError('Rolled-back draft persists')
                result.update(committed=False, rollback_verified=True)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    finally:
        frappe.db.rollback(); frappe.destroy()


if __name__ == '__main__': main()
