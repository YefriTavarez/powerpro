"""Import a hashed, bounded production export into DEV with native validations.

Default: insert and validate, then roll back. --apply explicitly commits only
the employee/checkins after checking unchanged automation and financial counts.
No credentials, HTTP requests, schema changes, or payroll actions belong here.
Source exports and receipts must remain outside the repository.
"""
import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import frappe

SITE = 'igcaribe.fortabs.com'
EMPLOYEE_FIELDS = ('first_name', 'middle_name', 'last_name', 'gender', 'date_of_birth',
                   'date_of_joining', 'status', 'company', 'department',
                   'employee_number', 'default_shift', 'holiday_list')
PUNCH_FIELDS = ('employee', 'time', 'log_type', 'shift', 'shift_start', 'shift_end',
                'shift_actual_start', 'shift_actual_end', 'offshift', 'skip_auto_attendance')
PROTECTED = ('Attendance', 'Overtime Authorization', 'Retroactive Overtime Adjustment',
             'Overtime Pay Policy', 'Overtime Reconciliation Run', 'Additional Salary',
             'Salary Slip', 'Leave Allocation', 'Leave Application',
             'Overtime Compensatory Credit', 'Overtime Settlement Election',
             'Email Queue', 'Notification Log')


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


def validate_bundle(bundle):
    if bundle['source_site'] != 'https://igcaribe.com':
        raise ValueError('Unexpected source site')
    employee, rows = bundle['employee'], bundle['checkins']
    begin, end = datetime.fromisoformat(bundle['start']), datetime.fromisoformat(bundle['end'])
    if not 0 < (end-begin).total_seconds() <= 7*86400 or not 1 <= len(rows) <= 200:
        raise ValueError('Sample must cover at most seven days and 200 checkins')
    if len({r['name'] for r in rows}) != len(rows):
        raise ValueError('Duplicate source names')
    identities = set()
    for row in rows:
        if row['employee'] != employee['name'] or not begin <= datetime.fromisoformat(row['time']) < end:
            raise ValueError('Checkin outside the selected employee/date scope')
        if row.get('log_type') not in ('IN', 'OUT') or row.get('attendance'):
            raise ValueError('Import requires explicit directions and no Attendance links')
        key = (row['time'], row['log_type'])
        if key in identities:
            raise ValueError('Duplicate employee/time/direction in source')
        identities.add(key)
    if employee.get('status') != 'Active':
        raise ValueError('The exported employee must be active')


def settings():
    return {dt: frappe.db.get_singles_dict(dt) for dt in
            ('System Settings', 'HR Settings', 'DGII Payroll Settings', 'Payroll Settings')}


def fingerprint(row, fields):
    return {key: str(row.get(key)) if row.get(key) is not None else None for key in fields}


def import_sample(bundle):
    if frappe.local.site != SITE or not frappe.conf.developer_mode or frappe.session.user != 'Administrator':
        raise frappe.PermissionError('Only Administrator on the explicit DEV site may run this CLI')
    validate_bundle(bundle)
    if frappe.db.get_single_value('System Settings', 'enable_scheduler') or frappe.db.get_single_value(
            'DGII Payroll Settings', 'enable_checkin_overtime_reconciliation'):
        raise ValueError('Pause DEV automation before importing a historical sample')
    employee, rows = bundle['employee'], bundle['checkins']
    shift_names = {r['shift'] for r in rows if r.get('shift')} | {employee['default_shift']}
    shifts = {name: frappe.get_doc('Shift Type', name).as_dict() for name in shift_names}
    if any(s.get('enable_auto_attendance') for s in shifts.values()):
        raise ValueError('Auto Attendance must remain disabled on every sample shift')
    before = {dt: frappe.db.count(dt) for dt in PROTECTED}
    before_settings = settings()
    totals = {dt: frappe.db.count(dt) for dt in ('Employee', 'Employee Checkin')}
    created_employee = False
    if frappe.db.exists('Employee', employee['name']):
        current = frappe.get_doc('Employee', employee['name'])
        if fingerprint(current, EMPLOYEE_FIELDS) != fingerprint(employee, EMPLOYEE_FIELDS):
            raise ValueError('Existing DEV employee differs; do not overwrite it')
    else:
        if frappe.db.exists('Employee', {'employee_number': employee['employee_number']}):
            raise ValueError('Employee number already belongs to another DEV record')
        current = frappe.get_doc({'doctype': 'Employee',
            **{key: employee.get(key) for key in EMPLOYEE_FIELDS}})
        current.insert(set_name=employee['name'])
        created_employee = True
    if current.name != employee['name'] or current.employee_name != employee['employee_name']:
        raise ValueError('Native employee identity differs from export')
    if fingerprint(current, EMPLOYEE_FIELDS) != fingerprint(employee, EMPLOYEE_FIELDS):
        raise ValueError('Native employee validation changed a source field')
    created, reused = [], []
    for row in sorted(rows, key=lambda r: (r['time'], r['name'])):
        if frappe.db.exists('Employee Checkin', row['name']):
            doc = frappe.get_doc('Employee Checkin', row['name'])
            reused.append(doc.name)
        else:
            if frappe.db.exists('Employee Checkin', {'employee': employee['name'], 'time': row['time']}):
                raise ValueError('Existing DEV timestamp has another name; review instead of duplicating')
            doc = frappe.get_doc({'doctype': 'Employee Checkin',
                **{key: row.get(key) for key in PUNCH_FIELDS}})
            doc.insert(set_name=row['name'])
            created.append(doc.name)
        if fingerprint(doc, PUNCH_FIELDS) != fingerprint(row, PUNCH_FIELDS) or doc.attendance:
            raise ValueError('Native shift/validation differs from source for ' + row['name'])
    if before != {dt: frappe.db.count(dt) for dt in PROTECTED} or before_settings != settings():
        raise ValueError('Protected documents or settings changed; roll back import')
    if any(canonical(s) != canonical(frappe.get_doc('Shift Type', name).as_dict()) for name, s in shifts.items()):
        raise ValueError('A shared shift changed during import')
    if frappe.db.count('Employee') != totals['Employee'] + int(created_employee):
        raise ValueError('Unexpected Employee count change')
    if frappe.db.count('Employee Checkin') != totals['Employee Checkin'] + len(created):
        raise ValueError('Unexpected checkin count change')
    return {'target_site': SITE, 'source_site': bundle['source_site'], 'employee': employee['name'],
            'employee_created': created_employee, 'created_checkins': created, 'reused_checkins': reused,
            'source_fields_verified': list(PUNCH_FIELDS), 'protected_counts': before,
            'settings_unchanged': True, 'shared_shifts_unchanged': True,
            'source_only_fields': 'accion and source creation/modified are retained in the bundle, not copied to unsupported DEV fields'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle')
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    raw = Path(args.bundle).read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.sha256:
        raise ValueError('Bundle hash does not match reviewed input')
    bundle = json.loads(raw)
    validate_bundle(bundle)
    frappe.init(site=SITE)
    frappe.connect()
    frappe.set_user('Administrator')
    commit = frappe.db.commit
    before_counts = {dt: frappe.db.count(dt) for dt in (*PROTECTED, 'Employee', 'Employee Checkin')}
    before_settings = settings()
    def forbidden(*args, **kwargs):
        raise AssertionError('Unexpected commit, queued job or outbound email')
    try:
        with (patch.object(frappe.db, 'commit', forbidden), patch.object(frappe, 'sendmail', forbidden),
              patch.object(frappe, 'enqueue', forbidden)):
            result = import_sample(bundle)
            repeated = import_sample(bundle)
            if repeated['employee_created'] or repeated['created_checkins']:
                raise AssertionError('Repeating the import was not idempotent')
            result['idempotent_retry_verified'] = True
        if args.apply:
            commit()
        else:
            frappe.db.rollback()
            after_counts = {dt: frappe.db.count(dt) for dt in before_counts}
            if after_counts != before_counts or settings() != before_settings:
                raise AssertionError('Dry-run rollback did not restore counts/settings')
            result['rollback_verified'] = True
        if args.apply:
            for row in bundle['checkins']:
                saved = frappe.get_doc('Employee Checkin', row['name'])
                if fingerprint(saved, PUNCH_FIELDS) != fingerprint(row, PUNCH_FIELDS):
                    raise AssertionError('Post-commit source readback differs')
            result['committed_readback_verified'] = True
        result.update(committed=args.apply, bundle_sha256=args.sha256)
        print(canonical(result))
    finally:
        frappe.db.rollback()
        frappe.destroy()


if __name__ == '__main__':
    main()
