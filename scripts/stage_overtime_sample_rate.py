"""Stage one source-backed hourly-rate assignment on the explicit DEV site.

This is a calculation fixture, not a complete payroll migration. Source files
and monetary values stay outside Git. Native insert/submit; default rollback.
"""
import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import frappe
from import_overtime_checkin_sample import SITE, PROTECTED, canonical, settings

DT = 'Salary Structure Assignment'
FIELDS = ('employee', 'company', 'salary_structure', 'from_date', 'base',
          'variable', 'currency', 'payroll_payable_account')


def stage(bundle, source_hash):
    from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import get_tax_component
    if frappe.local.site != SITE or not frappe.conf.developer_mode or frappe.session.user != 'Administrator':
        raise frappe.PermissionError('Explicit DEV Administrator required')
    if bundle['source_site'] != 'https://igcaribe.com' or bundle['mode'] != 'read_only' or len(bundle['assignments']) != 1:
        raise ValueError('One read-only production assignment required')
    row = bundle['assignments'][0]
    if row['employee'] != bundle['employee'] or row['docstatus'] != 1:
        raise ValueError('Wrong source identity/state')
    if any(day < row['from_date'] for day in bundle['work_dates']):
        raise ValueError('Source does not cover the sample')
    if frappe.db.get_single_value('System Settings', 'enable_scheduler'):
        raise ValueError('Keep DEV scheduler off')
    if get_tax_component(row['salary_structure']):
        raise ValueError('DEV structure needs tax configuration; do not omit it')
    structure = frappe.get_doc('Salary Structure', row['salary_structure'])
    source_structure = next(s for s in bundle['structures'] if s['name'] == structure.name)
    for key in ('company', 'currency', 'docstatus', 'is_active', 'payroll_frequency', 'salary_slip_based_on_timesheet'):
        if structure.get(key) != source_structure[key]:
            raise ValueError('DEV structure differs on ' + key)
    marker = 'DEV overtime rate sample; source SHA256: ' + source_hash
    existing = frappe.get_all(DT, filters={'employee': row['employee']}, pluck='name')
    if len(existing) > 1:
        raise ValueError('Review existing assignments first')
    created = not existing
    if existing:
        doc = frappe.get_doc(DT, existing[0])
        if not frappe.db.exists('Comment', {'reference_doctype': DT, 'reference_name': doc.name, 'content': ['like', marker + '%']}):
            raise ValueError('Existing assignment is not owned by this import')
    else:
        doc = frappe.get_doc({'doctype': DT, **{k: row.get(k) for k in FIELDS}})
        doc.insert()
        doc.submit()
        doc.add_comment('Comment', marker + '\nSource assignment: ' + row['name'] +
                        '\nHourly-rate fixture only. Source income tax slab, transportation and opening balances were not migrated. Not ready for Salary Slip generation.')
    doc.reload()
    for key in FIELDS:
        if key in ('base', 'variable'):
            if float(doc.get(key) or 0) != float(row.get(key) or 0): raise ValueError('Rate fixture differs')
        elif str(doc.get(key)) != str(row.get(key)): raise ValueError('Assignment differs on ' + key)
    if doc.docstatus != 1 or abs(float(doc.salary_per_hour) - float(row['salary_per_hour'])) > .00001:
        raise AssertionError('Native hourly calculation differs from production')
    return {'name': doc.name, 'created': created, 'docstatus': doc.docstatus,
            'hourly_rate': doc.salary_per_hour, 'currency': doc.currency,
            'source_assignment': row['name'], 'source_sha256': source_hash,
            'full_payroll_migration': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('--sha256', required=True)
    p.add_argument('--apply', action='store_true'); args = p.parse_args()
    raw = args.source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.sha256: raise ValueError('Source changed')
    bundle = json.loads(raw)
    frappe.init(site=SITE); frappe.connect(); frappe.set_user('Administrator')
    before_settings = settings()
    protected = (*PROTECTED, 'Employee', 'Employee Checkin')
    counts = {dt: frappe.db.count(dt) for dt in protected}
    original_assignments = {r.name: canonical(frappe.get_doc(DT, r.name).as_dict()) for r in frappe.get_all(DT)}
    def forbidden(*args, **kwargs): raise AssertionError('Outbound action attempted')
    try:
        with patch.object(frappe, 'sendmail', forbidden), patch.object(frappe, 'enqueue', forbidden):
            result = stage(bundle, args.sha256)
            if stage(bundle, args.sha256)['created']: raise AssertionError('Duplicate assignment')
            if settings() != before_settings or counts != {dt: frappe.db.count(dt) for dt in protected}:
                raise AssertionError('Settings or protected counts changed')
            if any(raw != canonical(frappe.get_doc(DT, name).as_dict()) for name, raw in original_assignments.items()):
                raise AssertionError('Existing assignment changed')
            if frappe.db.count(DT) != len(original_assignments) + int(result['created']):
                raise AssertionError('Unexpected assignment count')
            if args.apply:
                frappe.db.commit()
                if stage(bundle, args.sha256)['created']: raise AssertionError('Readback failed')
                result.update(committed=True, readback_verified=True)
            else:
                frappe.db.rollback()
                if frappe.db.count(DT) != len(original_assignments): raise AssertionError('Rollback failed')
                result.update(committed=False, rollback_verified=True)
            result.update(protected_counts=counts, idempotence_verified=True)
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    finally:
        frappe.db.rollback(); frappe.destroy()


if __name__ == '__main__': main()
