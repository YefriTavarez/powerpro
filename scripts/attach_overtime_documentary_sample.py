"""Attach a bounded, hashed documentary sample privately to a DEV Employee.

No approval, manual full-session declaration, payroll or settings changes.
The default exercises native File insertion and rollback; --apply commits.
Source documents and receipts stay outside Git. Repeated runs reuse exact files.
"""
import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import frappe

from import_overtime_checkin_sample import SITE, PROTECTED, canonical, settings


def sha(content):
    return hashlib.sha256(content).hexdigest()


def load_package(folder, expected_hash):
    raw = (folder / 'manifest.json').read_bytes()
    if sha(raw) != expected_hash:
        raise ValueError('Manifest changed')
    manifest = json.loads(raw)
    if manifest['site'] != SITE or not 1 <= len(manifest['files']) <= 3:
        raise ValueError('Explicit DEV site and at most three files required')
    files = {}
    for row in manifest['files']:
        name = row['name']
        if Path(name).name != name or Path(name).suffix not in {'.json', '.txt', '.png'} or name in files:
            raise ValueError('Unsafe or duplicate attachment name')
        content = (folder / name).read_bytes()
        if not content or len(content) > 10 * 1024 * 1024 or sha(content) != row['sha256']:
            raise ValueError('Attachment size or hash mismatch')
        files[name] = content
    return manifest, files


def attach(manifest, files):
    employee = manifest['employee']
    if frappe.local.site != SITE or not frappe.conf.developer_mode or frappe.session.user != 'Administrator':
        raise frappe.PermissionError('Explicit DEV Administrator required')
    doc = frappe.get_doc('Employee', employee)
    doc.check_permission('write')
    before_employee = canonical(doc.as_dict())
    before_settings = settings()
    before_counts = {dt: frappe.db.count(dt) for dt in (*PROTECTED, 'Employee', 'Employee Checkin')}
    punches = canonical(frappe.get_all('Employee Checkin', filters={'employee': employee}, fields=['*'], order_by='name'))
    records = []
    for name, content in files.items():
        matches = frappe.get_all('File', filters={'attached_to_doctype': 'Employee',
            'attached_to_name': employee, 'file_name': name}, pluck='name')
        if len(matches) > 1:
            raise ValueError('Multiple attachments have this name; review before proceeding')
        if matches:
            record = frappe.get_doc('File', matches[0])
            created = False
        else:
            record = frappe.get_doc({'doctype': 'File', 'file_name': name, 'is_private': 1,
                'attached_to_doctype': 'Employee', 'attached_to_name': employee, 'content': content})
            record.insert()
            created = True
        stored = record.get_content()
        if isinstance(stored, str):
            stored = stored.encode('utf-8')
        if not record.is_private or not record.file_url.startswith('/private/files/') or sha(stored) != sha(content):
            raise ValueError('Stored attachment content or privacy differs')
        records.append({'name': record.name, 'file_name': record.file_name, 'file_url': record.file_url,
                        'sha256': sha(stored), 'created': created, 'is_private': True})
    if before_settings != settings() or before_counts != {dt: frappe.db.count(dt) for dt in before_counts}:
        raise AssertionError('Protected settings or documents changed')
    if before_employee != canonical(frappe.get_doc('Employee', employee).as_dict()):
        raise AssertionError('Employee changed')
    if punches != canonical(frappe.get_all('Employee Checkin', filters={'employee': employee}, fields=['*'], order_by='name')):
        raise AssertionError('Checkins changed')
    return {'site': SITE, 'employee': employee, 'files': records, 'protected_counts': before_counts,
            'settings_unchanged': True, 'employee_unchanged': True, 'checkins_unchanged': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    manifest, files = load_package(args.folder, args.sha256)
    frappe.init(site=SITE)
    frappe.connect()
    frappe.set_user('Administrator')
    def forbidden(*args, **kwargs):
        raise AssertionError('Outbound action attempted')
    try:
        with patch.object(frappe, 'sendmail', forbidden), patch.object(frappe, 'enqueue', forbidden):
            result = attach(manifest, files)
            repeat = attach(manifest, files)
            if any(row['created'] for row in repeat['files']):
                raise AssertionError('Repeat created duplicates')
            result['idempotence_verified'] = True
            if args.apply:
                frappe.db.commit()
                readback = attach(manifest, files)
                if any(row['created'] for row in readback['files']):
                    raise AssertionError('Committed attachment missing')
                result.update(committed=True, readback_verified=True)
            else:
                frappe.db.rollback()
                for row in result['files']:
                    if row['created'] and frappe.db.exists('File', row['name']):
                        raise AssertionError('Rollback failed')
                result.update(committed=False, rollback_verified=True)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    finally:
        frappe.db.rollback()
        frappe.destroy()


if __name__ == '__main__':
    main()
