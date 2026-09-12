"""Reproduce one archived production shift's calendar fields on explicit DEV.

Adds neutral optional metadata, then saves only the named shift and selected
drafts. DDL is not transactional: keep the receipt and leave neutral fields on
failure. No migration, production access, scheduler, checkin or payment action.
"""
import argparse
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import frappe
from import_overtime_checkin_sample import SITE, PROTECTED, canonical, settings

TAG = 'PowerPro DEV documentary pilot: neutral optional schedule metadata.'
CONTROL = 'custom_control_dias_laborables'
FRIDAY = 'custom_hora_salida_viernes'
DAYS = ('lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo')
FIELDS = (CONTROL, FRIDAY, *('custom_trabaja_' + day for day in DAYS))


def contexts(shift, holiday_list):
    from powerpro.controllers.overtime import get_schedule_context
    first = date(2026, 1, 1)
    return canonical([get_schedule_context(first + timedelta(days=n), shift, holiday_list) for n in range(365)])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('--sha256', required=True)
    p.add_argument('--employee', required=True); p.add_argument('--drafts', nargs=3, required=True)
    p.add_argument('--receipt', type=Path, required=True); p.add_argument('--apply', action='store_true')
    args = p.parse_args(); raw = args.source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.sha256: raise ValueError('Source archive changed')
    source = json.loads(raw)
    values = {key: source[key] for key in FIELDS}
    if values[CONTROL] != 1: raise ValueError('Archived explicit weekday control required')
    frappe.init(site=SITE); frappe.connect(); frappe.set_user('Administrator')
    def forbidden(*args, **kwargs): raise AssertionError('Outbound action attempted')
    try:
        if not frappe.conf.developer_mode: raise ValueError('DEV required')
        if frappe.db.get_single_value('System Settings', 'enable_scheduler') or frappe.db.get_single_value(
                'DGII Payroll Settings', 'enable_checkin_overtime_reconciliation'):
            raise ValueError('Keep automation disabled')
        employee = frappe.get_doc('Employee', args.employee)
        if employee.default_shift != source['name']: raise ValueError('Unexpected employee shift')
        before_settings = settings()
        before_counts = {dt: frappe.db.count(dt) for dt in (*PROTECTED, 'Employee', 'Employee Checkin')}
        before_punches = canonical(frappe.get_all('Employee Checkin', fields=['*'], order_by='name'))
        old_shifts = {row.name: frappe.get_doc('Shift Type', row.name).as_dict() for row in frappe.get_all('Shift Type')}
        if any(row.get('enable_auto_attendance') for row in old_shifts.values()):
            raise ValueError('Auto Attendance must remain off for DEV calendar setup')
        baseline = {name: contexts(name, row.get('holiday_list') or employee.holiday_list)
                    for name, row in old_shifts.items() if name != source['name']}
        old_drafts = {name: frappe.get_doc('Retroactive Overtime Adjustment', name).as_dict() for name in args.drafts}
        for row in old_drafts.values():
            if row['employee'] != args.employee or row['docstatus'] != 0 or row.get('verified_hours'):
                raise ValueError('Only the selected unverified employee drafts may be refreshed')
        definitions = []
        for key in FIELDS:
            fieldtype = 'Time' if key == FRIDAY else 'Check'
            existing = frappe.get_meta('Shift Type').get_field(key)
            if existing:
                if existing.fieldtype != fieldtype or existing.description != TAG:
                    raise ValueError('Existing schedule field is not owned by this DEV installer: ' + key)
                continue
            definitions.append({'fieldname': key, 'fieldtype': fieldtype, 'insert_after': 'end_time',
                'label': 'Salida del viernes' if key == FRIDAY else ('Usar días laborables configurados' if key == CONTROL else key.replace('custom_trabaja_', 'Trabaja ').capitalize()),
                'description': TAG, **({'default': '0'} if fieldtype == 'Check' else {})})
        receipt = {'site': SITE, 'shift': source['name'], 'source_sha256': args.sha256,
                   'settings_unchanged': False, 'shift_before': old_shifts[source['name']],
                   'target_fields': values, 'new_fields': [f['fieldname'] for f in definitions],
                   'drafts_before': old_drafts, 'committed': False, 'metadata_ddl_not_transactional': True}
        args.receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, default=str))
        args.receipt.chmod(0o600)
        if not args.apply:
            print(json.dumps({'preflight': 'passed', 'shift': source['name'], 'new_fields': receipt['new_fields']})); return
        with patch.object(frappe, 'sendmail', forbidden), patch.object(frappe, 'enqueue', forbidden):
            from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
            if definitions:
                create_custom_fields({'Shift Type': definitions}, ignore_validate=False, update=False)
                frappe.db.commit()
            shift = frappe.get_doc('Shift Type', source['name'])
            shift.update(values); shift.save()
            for name in args.drafts:
                frappe.get_doc('Retroactive Overtime Adjustment', name).save()
            for name, before in baseline.items():
                if before != contexts(name, old_shifts[name].get('holiday_list') or employee.holiday_list):
                    raise AssertionError('Another shift calendar changed')
            for name, old in old_shifts.items():
                new = frappe.get_doc('Shift Type', name).as_dict()
                for key, value in old.items():
                    if key not in (*FIELDS, 'modified', 'modified_by') and canonical(value) != canonical(new.get(key)):
                        raise AssertionError('Unrelated shift field changed: ' + key)
            if before_settings != settings() or before_counts != {dt: frappe.db.count(dt) for dt in before_counts}:
                raise AssertionError('Protected settings or documents changed')
            if before_punches != canonical(frappe.get_all('Employee Checkin', fields=['*'], order_by='name')):
                raise AssertionError('Checkins changed')
            from powerpro.controllers.overtime import get_schedule_context
            actual = {day: get_schedule_context(day, source['name'], employee.holiday_list) for day in ['2026-08-14', '2026-08-15', '2026-08-16']}
            if actual['2026-08-14']['shift_end'].hour != 17 or actual['2026-08-15']['classification'] != 'Weekly Rest' or actual['2026-08-16']['classification'] != 'Legal Holiday on Weekly Rest':
                raise AssertionError('Archived sample calendar was not reproduced')
            frappe.db.commit()
            receipt.update(committed=True, settings_unchanged=True, checkins_unchanged=True,
                           other_shift_full_year_unchanged=True, protected_counts=before_counts,
                           sample_contexts=actual, refreshed_drafts=args.drafts)
            args.receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, default=str))
            print(json.dumps({k: receipt[k] for k in ['committed','sample_contexts','settings_unchanged','checkins_unchanged','other_shift_full_year_unchanged']}, default=str))
    finally:
        frappe.db.rollback(); frappe.destroy()


if __name__ == '__main__': main()
