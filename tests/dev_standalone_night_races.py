"""DEV-only independent connections with stale snapshots and contended employee locks.

Commits uniquely owned fixtures, then removes only those documents. Global flags
remain off; workers opt in only in memory. Never run on a production site.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

import frappe
from frappe.utils import get_datetime

SITE = 'igcaribe.fortabs.com'
frappe.init(site=SITE)
frappe.connect()
frappe.set_user('Administrator')
assert frappe.local.site == SITE and frappe.conf.developer_mode
from powerpro.controllers import ordinary_night as night, ordinary_night_automation as auto


def forbidden(*args, **kwargs):
    raise AssertionError('Outbound effects forbidden in DEV concurrency fixtures')


frappe.sendmail = forbidden
frappe.enqueue = forbidden
frappe.publish_realtime = lambda *args, **kwargs: None
errors = []
frappe.log_error = lambda *args, **kwargs: errors.append((args, kwargs))
assert not frappe.db.get_single_value('DGII Payroll Settings', 'enable_checkin_overtime_reconciliation')


def wait_for(path):
    deadline = time.monotonic() + 25
    while not Path(path).exists():
        assert time.monotonic() < deadline, 'Barrier timeout: ' + path
        time.sleep(.02)


if len(sys.argv) > 1:
    schedule, action, barrier, slot = sys.argv[1:]
    get_single, get_single_value, get_doc = frappe.get_single, frappe.db.get_single_value, frappe.get_doc

    def settings(dt, *args, **kwargs):
        doc = get_single(dt, *args, **kwargs)
        if dt == 'DGII Payroll Settings':
            doc.enable_checkin_overtime_reconciliation = 1
            doc.checkin_overtime_effective_from = '2026-09-01'
        return doc

    def setting(dt, field, *args, **kwargs):
        if dt == 'DGII Payroll Settings':
            if field == 'enable_checkin_overtime_reconciliation':
                return 1
            if field == 'checkin_overtime_effective_from':
                return '2026-09-01'
        return get_single_value(dt, field, *args, **kwargs)

    def script_doc(dt, *args, **kwargs):
        doc = get_doc(dt, *args, **kwargs)
        if dt == 'DGII Payroll Settings':
            doc.enable_checkin_overtime_reconciliation = 1
            doc.checkin_overtime_effective_from = '2026-09-01'
        return doc

    # Native services use get_single; Server Scripts use the exposed get_doc API.
    # Keep the global switch off and opt in only these fixture worker processes.
    frappe.get_single, frappe.db.get_single_value, frappe.get_doc = settings, setting, script_doc
    night.now_datetime = auto.now_datetime = lambda: get_datetime('2026-09-20 10:00:00')
    doc = frappe.get_doc(auto.DT, schedule)
    assert doc.reference.startswith('STANDALONE-RACE-DEV-')
    # Read settlement/enrollment state before either worker obtains its lock.
    frappe.db.count(night.DT)
    frappe.db.count(auto.DT)
    original_get_value = frappe.db.get_value
    intercepted = False

    def lock_probe(doctype, *args, **kwargs):
        global intercepted
        first = doctype == 'Employee' and kwargs.get('for_update') and not intercepted
        if first:
            intercepted = True
            Path(barrier + '.' + slot + '.attempt').touch()
        value = original_get_value(doctype, *args, **kwargs)
        if first:
            Path(barrier + '.' + slot + '.locked').touch()
            if slot == 'holder':
                wait_for(barrier + '.release')
        return value

    frappe.db.get_value = lock_probe
    Path(barrier + '.' + slot + '.ready').touch()
    wait_for(barrier + '.' + slot + '.go')
    try:
        if action == 'submit':
            doc.submit()
            result = {'status': 'Submitted'}
        elif action == 'manual':
            settlement = frappe.get_doc({'doctype': night.DT, 'employee': doc.employee,
                'work_date': str(doc.from_date), 'settlement_payroll_date': str(doc.settlement_payroll_date),
                'review_reference': doc.reference})
            settlement.insert()
            settlement.submit()
            result = {'status': 'Manual', 'settlement': settlement.name}
        elif action == 'cancel':
            doc.cancel()
            result = {'status': 'Cancelled'}
        else:
            result = auto.process_day(doc.name, doc.from_date)
        frappe.db.commit()
    except frappe.ValidationError as exc:
        frappe.db.rollback()
        result = {'status': 'Rejected', 'message': str(exc)}
    finally:
        assert not errors, errors
        frappe.db.rollback()
        frappe.destroy()
    print(json.dumps(result, default=str))
    raise SystemExit()


assert not frappe.db.count(auto.DT)
assert not frappe.db.count(night.DT)
assert not frappe.db.count('Overtime Pay Policy', {'docstatus': 1})
types = ['Employee', 'Shift Type', 'Employee Checkin', 'Salary Structure Assignment', 'Overtime Pay Policy',
    'Overtime Work Call', 'Overtime Authorization', auto.DT, auto.DAY, night.DT, 'Additional Salary',
    'Overtime Reconciliation Run', 'Salary Slip', 'Error Log', 'Notification Log', 'Version', 'Comment']
baseline = {dt: frappe.db.count(dt) for dt in types}
settings_before = frappe.db.get_singles_dict('DGII Payroll Settings')
prefix = 'STANDALONE-RACE-DEV-' + uuid.uuid4().hex[:10]
owned = []
employee_name = prefix + '-EMP'
processes = []
barriers = []


def race(schedules, actions):
    barrier = '/tmp/' + prefix + '-' + uuid.uuid4().hex[:6]
    barriers.append(barrier)
    running = [subprocess.Popen([sys.executable, __file__, name, action, barrier, slot],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for name, action, slot in zip(schedules, actions, ['holder', 'waiter'])]
    processes.extend(running)
    def stage(path):
        deadline = time.monotonic() + 25
        while not Path(path).exists():
            for proc in running:
                if proc.poll() is not None:
                    raise AssertionError(('Worker exited before barrier', path, proc.communicate()))
            assert time.monotonic() < deadline, 'Barrier timeout: ' + path
            time.sleep(.02)
    for slot in ['holder', 'waiter']:
        stage(barrier + '.' + slot + '.ready')
    Path(barrier + '.holder.go').touch()
    stage(barrier + '.holder.locked')
    Path(barrier + '.waiter.go').touch()
    stage(barrier + '.waiter.attempt')
    # The holder still owns the employee lock when the second connection asks for it.
    assert not Path(barrier + '.waiter.locked').exists()
    Path(barrier + '.release').touch()
    results = []
    for proc in running:
        out, err = proc.communicate(timeout=35)
        assert proc.returncode == 0, (out, err)
        results.append(json.loads(out.strip()))
    frappe.db.rollback()
    return results


try:
    base = frappe.get_doc('Overtime Authorization', 'AUT-HE-2026-00018')
    shift = frappe.copy_doc(frappe.get_doc('Shift Type', 'Diurna Extendida'))
    shift.name = prefix + '-SHIFT'
    shift.docstatus = 0
    shift.start_time, shift.end_time = '18:00:00', '02:00:00'
    # This synthetic overnight schedule must not inherit the daytime shift's
    # special Friday exit (17:00), which would create a 23-hour work window.
    shift.custom_hora_salida_viernes = None
    shift.enable_auto_attendance = 0
    shift.begin_check_in_before_shift_start_time = shift.allow_check_out_after_shift_end_time = 0
    shift.determine_check_in_and_check_out = 'Alternating entries as IN and OUT during the same shift'
    shift.working_hours_calculation_based_on = 'Every Valid Check-in and Check-out'
    shift.last_sync_of_checkin = '2026-09-30 23:00:00'
    shift.db_insert()
    owned.append((shift.doctype, shift.name))
    employee = frappe.copy_doc(frappe.get_doc('Employee', base.employee))
    employee.name, employee.employee_name, employee.docstatus = employee_name, 'DEV Night Concurrent', 0
    employee.user_id = employee.company_email = employee.personal_email = None
    employee.default_shift, employee.status = shift.name, 'Active'
    employee.db_insert()
    owned.append((employee.doctype, employee.name))
    name = frappe.get_all('Salary Structure Assignment', filters={'employee': base.employee, 'docstatus': 1},
        pluck='name', order_by='from_date desc', limit=1)[0]
    assignment = frappe.copy_doc(frappe.get_doc('Salary Structure Assignment', name))
    assignment.name, assignment.employee, assignment.docstatus = prefix + '-SSA', employee.name, 1
    assignment.from_date, assignment.base, assignment.salary_per_hour = '2026-01-01', 19064, 100
    assignment.db_insert()
    owned.append((assignment.doctype, assignment.name))
    policy = frappe.get_doc({'doctype': 'Overtime Pay Policy', 'title': prefix, 'company': employee.company,
        'valid_from': '2026-09-01', 'valid_until': '2026-09-30', 'approval_reference': prefix + ' synthetic test only',
        'weekly_threshold': 68, 'regular_percent': 35, 'extraordinary_percent': 100, 'night_percent': 15,
        'weekly_rest_percent': 100, 'night_basis': 'Clock overlap', 'premium_combination': 'Additive on base hour',
        'enable_compensatory': 0, 'auto_ordinary_night': 1})
    policy.insert()
    owned.append((policy.doctype, policy.name))
    policy.submit()
    for day in [14, 15, 16, 17, 18]:
        for stamp, kind in [(f'2026-09-{day} 18:00:00', 'IN'), (f'2026-09-{day+1} 02:00:00', 'OUT')]:
            punch = frappe.get_doc({'doctype': 'Employee Checkin', 'employee': employee.name, 'time': stamp, 'log_type': kind})
            punch.insert()
            owned.append((punch.doctype, punch.name))

    def schedule(day, submit=False):
        doc = frappe.get_doc({'doctype': auto.DT, 'employee': employee.name, 'from_date': f'2026-09-{day}',
            'to_date': f'2026-09-{day}', 'settlement_payroll_date': '2026-09-20', 'policy': policy.name,
            'reference': prefix, 'enabled': 1})
        doc.insert()
        owned.append((doc.doctype, doc.name))
        if submit:
            doc.submit()
        return doc.name

    first, duplicate = schedule(14), schedule(14)
    manual, cancelled = schedule(15, True), schedule(16, True)
    late_cancel, two_manual = schedule(17, True), schedule(18, True)
    frappe.db.commit()
    results = race([first, duplicate], ['submit', 'submit'])
    assert [r['status'] for r in results] == ['Submitted', 'Rejected'], results
    assert frappe.db.count(auto.DT, {'employee': employee.name, 'from_date': '2026-09-14', 'docstatus': 1}) == 1
    print('Concurrent overlapping enrollments: exactly one approved', flush=True)

    results = race([first, first], ['process', 'process'])
    assert [r['status'] for r in results] == ['Created', 'Created'], results
    assert results[0]['settlement'] == results[1]['settlement'], results
    print('Concurrent automatic runs: one settlement and one earning', flush=True)

    results = race([manual, manual], ['manual', 'process'])
    assert [r['status'] for r in results] == ['Manual', 'Existing'], results
    assert results[0]['settlement'] == results[1]['settlement'], results
    print('Manual submit versus old automatic snapshot: existing claim recognized', flush=True)

    results = race([cancelled, cancelled], ['cancel', 'process'])
    assert [r['status'] for r in results] == ['Cancelled', 'Paused'], results
    assert not frappe.db.count(night.DT, {'employee': employee.name, 'work_date': '2026-09-16'})
    results = race([late_cancel, late_cancel], ['process', 'cancel'])
    assert [r['status'] for r in results] == ['Created', 'Cancelled'], results
    history = frappe.get_doc(auto.DT, late_cancel)
    assert history.docstatus == 2 and history.days[0].status == 'Created', history.as_dict()
    assert history.days[0].settlement == results[0]['settlement']
    assert frappe.db.get_value(night.DT, results[0]['settlement'], 'docstatus') == 1
    print('Cancellation after processing preserves the earning and daily audit', flush=True)

    results = race([two_manual, two_manual], ['manual', 'manual'])
    assert [r['status'] for r in results] == ['Manual', 'Rejected'], results
    print('Two manual submissions: exactly one approved claim', flush=True)
    settlements = frappe.get_all(night.DT, filters={'employee': employee.name, 'docstatus': 1}, fields=['name', 'settlement_amount'])
    salaries = frappe.get_all('Additional Salary', filters={'employee': employee.name, 'docstatus': 1}, fields=['amount', 'ref_doctype', 'ref_docname'])
    assert len(settlements) == len(salaries) == 4 and all(s.settlement_amount == 75 for s in settlements), (settlements, salaries)
    assert all(s.amount == 75 and s.ref_doctype == night.DT for s in salaries), salaries
    assert frappe.db.count('Overtime Authorization') == baseline['Overtime Authorization']
    assert not errors, errors
    print('STANDALONE_RACES_PASS: both cancellation orders, four independent nights, four synthetic75 earnings; no overtime created')
finally:
    for proc in processes:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    for barrier in barriers:
        for path in Path('/tmp').glob(Path(barrier).name + '*'):
            path.unlink()
    frappe.db.rollback()
    for dt in [night.DT, 'Additional Salary', 'Overtime Reconciliation Run']:
        owned.extend((dt, name) for name in frappe.get_all(dt, filters={'employee': employee_name}, pluck='name'))
    for dt, name in reversed(owned):
        for field in frappe.get_meta(dt).get_table_fields():
            frappe.db.delete(field.options, {'parent': name, 'parenttype': dt})
        for audit, filters in [('Version', {'ref_doctype': dt, 'docname': name}),
                ('Comment', {'reference_doctype': dt, 'reference_name': name}),
                ('DocShare', {'share_doctype': dt, 'share_name': name})]:
            frappe.db.delete(audit, filters)
        frappe.db.delete(dt, {'name': name})
    frappe.db.commit()
    after = {dt: frappe.db.count(dt) for dt in types}
    assert baseline == after, (baseline, after)
    assert settings_before == frappe.db.get_singles_dict('DGII Payroll Settings')
    print('STANDALONE_RACES_CLEANUP', json.dumps(after))
    frappe.db.rollback()
    frappe.destroy()
