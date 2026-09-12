"""DEV read-only comparison of imported punches and confirmed paper windows.

Uses the real evidence engine, both DEV schedule and archived production
schedule. A separately labelled scenario advances only an in-memory sync
watermark; it never certifies synchronization, weekly evidence, or payment.
"""
import argparse
from copy import deepcopy
from datetime import date, datetime, timedelta
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import frappe
from import_overtime_checkin_sample import SITE, PROTECTED, PUNCH_FIELDS, fingerprint, settings, validate_bundle


def source_context(bundle, day):
    from powerpro.payroll_rules.overtime import classify_workday, get_shift_window
    shift = bundle['shift']
    weekday = ('lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo')[day.weekday()]
    holidays = [r for r in bundle['calendar']['holidays'] if r['holiday_date'] == day.isoformat()]
    workday_field = 'custom_trabaja_' + weekday
    is_workday = bool(shift[workday_field]) if workday_field in shift else not any(r.get('weekly_off') for r in holidays)
    is_holiday = any(not r.get('weekly_off') or r.get('custom_is_legal_holiday') for r in holidays)
    start, end = get_shift_window(day, shift['start_time'], shift['end_time'], shift.get('custom_hora_salida_viernes'))
    return {'date': day.isoformat(), 'shift_start': start, 'shift_end': end,
            'classification': classify_workday(is_shift_workday=is_workday, has_legal_holiday=is_holiday),
            'holiday_list_covers_work_date': bundle['calendar']['from_date'] <= str(day) <= bundle['calendar']['to_date']}


def preview(bundle):
    from powerpro.controllers.overtime import get_schedule_context
    from powerpro.payroll_rules.overtime_evidence import evaluate_evidence
    if frappe.local.site != SITE or not frappe.conf.developer_mode:
        raise ValueError('Explicit DEV site required')
    validate_bundle(bundle)
    counts = {dt: frappe.db.count(dt) for dt in (*PROTECTED, 'Employee', 'Employee Checkin')}
    config = settings()
    live_rows = [frappe.get_doc('Employee Checkin', r['name']).as_dict() for r in bundle['checkins']]
    for actual, original in zip(live_rows, bundle['checkins']):
        if fingerprint(actual, PUNCH_FIELDS) != fingerprint(original, PUNCH_FIELDS):
            raise ValueError('Imported evidence changed: ' + original['name'])
    cases = []
    for window in bundle['paper_windows']:
        day = date.fromisoformat(window['date'])
        start, end = datetime.fromisoformat(window['start']), datetime.fromisoformat(window['end'])
        authorization = {'name': 'UNSAVED-PAPER-' + str(day), 'start': start, 'end': end,
                         'shift': bundle['shift']['name'], 'maximum_hours': (end-start).total_seconds()/3600}
        rows = [r for r in bundle['checkins'] if r['time'][:10] == str(day)]
        source = source_context(bundle, day)
        dev = dict(get_schedule_context(day, bundle['shift']['name'], bundle['employee']['holiday_list']), date=str(day))
        scenarios = []
        for label, context, shift in [('current_dev', dev, frappe.get_doc('Shift Type', bundle['shift']['name']).as_dict()),
                                       ('archived_production', source, bundle['shift'])]:
            for sync_complete in (False, True):
                policy = deepcopy(shift)
                if sync_complete:
                    policy['last_sync_of_checkin'] = end + timedelta(days=1)
                result = evaluate_evidence(authorization=authorization, rows=rows, shift=policy,
                    contexts=[context], next_windows=[], now=datetime.now(), context_complete=True)
                scenarios.append({'schedule_source': label, 'hypothetical_sync_complete': sync_complete,
                                  'result': result, 'settlement_ready': False, 'weekly_evidence_checked': False})
        cases.append({'date': str(day), 'paper_window': window, 'source_context': source, 'dev_context': dev,
                      'scenarios': scenarios,
                      'existing_production_adjustments': [r for r in bundle['production_adjustments'] if r['work_date'] == str(day)]})
    if config != settings() or counts != {dt: frappe.db.count(dt) for dt in counts}:
        raise AssertionError('Site settings or counts changed during preview')
    for original in bundle['checkins']:
        actual = frappe.get_doc('Employee Checkin', original['name'])
        if fingerprint(actual, PUNCH_FIELDS) != fingerprint(original, PUNCH_FIELDS):
            raise AssertionError('Source changed during preview')
    return {'site': SITE, 'read_only': True, 'employee': bundle['employee']['name'], 'cases': cases,
            'counts_unchanged': counts, 'settings_unchanged': True, 'source_readback_verified': True,
            'settlement_ready': False, 'disclaimer': 'In-memory sync-complete scenarios are diagnostics only; no weekly bands or payments are certified.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle')
    parser.add_argument('--sha256', required=True)
    args = parser.parse_args()
    raw = Path(args.bundle).read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.sha256:
        raise ValueError('Bundle hash changed')
    frappe.init(site=SITE)
    frappe.connect()
    sql = frappe.db.sql
    def read_sql(query, *args, **kwargs):
        if not str(query).lstrip().lower().startswith(('select', 'show', 'describe', 'explain')):
            raise AssertionError('Non-read SQL attempted')
        return sql(query, *args, **kwargs)
    def forbidden(*args, **kwargs):
        raise AssertionError('Commit or outbound action attempted')
    try:
        with (patch.object(frappe.db, 'sql', read_sql), patch.object(frappe.db, 'commit', forbidden),
              patch.object(frappe, 'sendmail', forbidden), patch.object(frappe, 'enqueue', forbidden)):
            result = preview(json.loads(raw))
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str, indent=2))
    finally:
        frappe.db.rollback()
        frappe.destroy()


if __name__ == '__main__':
    main()
