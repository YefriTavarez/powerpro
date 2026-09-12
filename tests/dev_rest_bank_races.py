"""DEV-only independent connections with stale snapshots and contended employee locks.

Commits uniquely owned fixtures, then removes only those documents. Global evidence reconciliation
remains off; workers opt in only in memory. Never run on a production site.
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
from powerpro.controllers import checkin_overtime as evidence, overtime_rest as rest, overtime_compensatory_settlement as bank, retroactive_evidence as retro


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


from powerpro.power_pro.doctype.retroactive_overtime_adjustment import retroactive_overtime_adjustment as retro_controller
MIXED = os.environ.get('REST_BANK_MIXED') == '1'
get_single, get_single_value = frappe.get_single, frappe.db.get_single_value

def settings(dt, *args, **kwargs):
    doc = get_single(dt, *args, **kwargs)
    if dt == 'DGII Payroll Settings':
        doc.enable_checkin_overtime_reconciliation = 1
        doc.checkin_overtime_effective_from = '2026-09-01'
        doc.enable_overtime_compensatory_settlement = 1
        doc.enable_retroactive_overtime_adjustment = 1
        doc.retroactive_overtime_from_date = '2026-09-01'
        doc.retroactive_overtime_to_date = '2026-09-30'
        doc.retroactive_overtime_submission_deadline = '2026-09-30'
    if dt == 'HR Settings':
        doc.send_leave_notification = 0
    return doc

def setting(dt, field, *args, **kwargs):
    if dt == 'DGII Payroll Settings':
        if field in ['enable_checkin_overtime_reconciliation', 'enable_overtime_compensatory_settlement']:
            return 1
        if field == 'checkin_overtime_effective_from':
            return '2026-09-01'
        if field == 'enable_retroactive_overtime_adjustment':
            return 1
        if field == 'retroactive_overtime_from_date':
            return '2026-09-01'
        if field in ['retroactive_overtime_to_date','retroactive_overtime_submission_deadline']:
            return '2026-09-30'
    if dt == 'HR Settings' and field == 'send_leave_notification':
        return 0
    return get_single_value(dt, field, *args, **kwargs)

settings_before = {dt: frappe.db.get_singles_dict(dt) for dt in ['DGII Payroll Settings','HR Settings']}
frappe.get_single, frappe.db.get_single_value = settings, setting
evidence.now_datetime = rest.now_datetime = lambda: get_datetime('2026-09-20 10:00:00')
rest.now_datetime = lambda: get_datetime('2026-09-24 10:00:00')
retro.now_datetime = retro_controller.now_datetime = evidence.now_datetime

if len(sys.argv) > 1:
    payload, action, barrier, slot = sys.argv[1:]
    data = json.loads(payload)
    ref = frappe.get_doc(data.get('source_type', 'Overtime Authorization'), data['auth'])
    assert ref.employee.startswith('REST-BANK-RACE-DEV-')
    frappe.db.count('Overtime Compensatory Credit')
    frappe.db.count('Overtime Settlement Election')
    original_get_value = frappe.db.get_value
    intercepted = False

    def lock_probe(doctype, *args, **kwargs):
        global intercepted
        first = doctype == data.get('mutex_doctype', 'Employee') and kwargs.get('for_update') and not intercepted
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
        if action == 'settle':
            if ref.doctype == retro.DT:
                result = retro.create_compensatory_settlement(ref.name)
                assert result['settlement_status'] == 'Credited', result
                result = {'status': 'Frozen', 'source_type': retro.DT}
            else:
                result = {'status': evidence.process_authorization(ref.name)}
        elif action == 'link':
            result = rest.link_leave(data['election'], data['leave'])
        elif action == 'cancel_leave':
            doc = frappe.get_doc('Leave Application', data['leave'])
            doc.cancel()
            result = {'status': 'Leave Cancelled'}
        elif action == 'submit_leave':
            doc = frappe.get_doc('Leave Application', data['leave'])
            doc.submit()
            result = {'status': 'Leave Submitted'}
        elif action == 'enjoy':
            election = frappe.get_doc('Overtime Settlement Election', data['election'])
            result = rest.confirm_enjoyment(election.name, election.planned_start, election.planned_end,
                ref.employee + ' synthetic enjoyment verification')
        else:
            doc = frappe.get_doc(ref.doctype, ref.name)
            doc.cancel()
            result = {'status': 'Cancelled'}
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

types = ['Employee', 'Shift Type', 'Employee Checkin', 'Salary Structure Assignment', 'Overtime Pay Policy',
    'Overtime Work Call', 'Overtime Authorization', 'Retroactive Overtime Adjustment', 'Overtime Settlement Election', 'Overtime Compensatory Credit', 'Additional Salary', 'Leave Period', 'Leave Allocation', 'Leave Application', 'Leave Ledger Entry', 'Attendance',
    'Overtime Reconciliation Run', 'Salary Slip', 'Error Log', 'Notification Log', 'Version', 'Comment']
baseline = {dt: frappe.db.count(dt) for dt in types}
prefix = 'REST-BANK-RACE-DEV-' + uuid.uuid4().hex[:10]
owned = []
employee_name = prefix + '-EMP'
processes = []
barriers = []


def race(schedules, actions):
    barrier = '/tmp/' + prefix + '-' + uuid.uuid4().hex[:6]
    barriers.append(barrier)
    running = [subprocess.Popen([sys.executable, __file__, json.dumps(name), action, barrier, slot],
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
    # The holder still owns the shared lock when the second connection asks for it.
    assert not Path(barrier + '.waiter.locked').exists()
    Path(barrier + '.release').touch()
    results = []
    for proc in running:
        out, err = proc.communicate(timeout=35)
        assert proc.returncode == 0, (out, err)
        results.append(json.loads(out.strip()))
    frappe.db.rollback()
    return results

assert not frappe.db.count('Overtime Compensatory Credit')
assert not frappe.db.count('Overtime Settlement Election')
assert not frappe.db.count('Overtime Pay Policy', {'docstatus': 1})
assert not frappe.db.count('Leave Period')
try:
    base = frappe.get_doc('Overtime Authorization', 'AUT-HE-2026-00018')
    shift = frappe.copy_doc(frappe.get_doc('Shift Type', 'Diurna Extendida'))
    shift.name, shift.docstatus, shift.enable_auto_attendance = prefix + '-SHIFT', 0, 0
    shift.determine_check_in_and_check_out = 'Alternating entries as IN and OUT during the same shift'
    shift.working_hours_calculation_based_on = 'Every Valid Check-in and Check-out'
    shift.last_sync_of_checkin = '2026-09-30 23:00:00'
    shift.db_insert()
    owned.append((shift.doctype, shift.name))
    employee = frappe.copy_doc(frappe.get_doc('Employee', base.employee))
    employee.name, employee.employee_name, employee.docstatus = employee_name, 'DEV Rest Concurrent', 0
    employee.user_id = employee.company_email = employee.personal_email = None
    employee.default_shift, employee.status = shift.name, 'Active'
    employee.overtime_approver = 'Administrator'
    employee.db_insert()
    owned.append((employee.doctype, employee.name))
    name = frappe.get_all('Salary Structure Assignment', filters={'employee': base.employee, 'docstatus': 1},
        pluck='name', order_by='from_date desc', limit=1)[0]
    assignment = frappe.copy_doc(frappe.get_doc('Salary Structure Assignment', name))
    assignment.name, assignment.employee, assignment.docstatus = prefix + '-SSA', employee.name, 1
    assignment.from_date, assignment.base, assignment.salary_per_hour = '2026-01-01', 19064, 100
    assignment.db_insert()
    owned.append((assignment.doctype, assignment.name))
    leave_type = get_single_value('DGII Payroll Settings','overtime_compensatory_leave_type')
    policy = frappe.get_doc({'doctype': 'Overtime Pay Policy', 'title': prefix, 'company': employee.company,
        'valid_from': '2026-09-01', 'valid_until': '2026-09-30', 'approval_reference': prefix + ' synthetic test only',
        'weekly_threshold': 68, 'regular_percent': 35, 'extraordinary_percent': 100, 'night_percent': 15,
        'weekly_rest_percent': 100, 'night_basis': 'Clock overlap', 'premium_combination': 'Additive on base hour',
        'enable_compensatory': 1, 'leave_type': leave_type, 'hours_per_leave_day': 8, 'leave_increment': .5,
        'rest_hours_per_worked_hour': 1, 'weekly_rest_duration_hours': 36, 'weekly_rest_credit_hours': 8})
    policy.insert()
    owned.append((policy.doctype, policy.name))
    policy.submit()
    period = frappe.get_doc({'doctype': 'Leave Period', 'company': employee.company,
        'from_date': '2026-01-01', 'to_date': '2026-12-31', 'is_active': 1})
    period.insert()
    owned.append((period.doctype, period.name))
    for day, end in [(14, '20:00:00'), (15, '21:00:00')]:
        for clock, kind in [('08:00:00', 'IN'), (end, 'OUT')]:
            punch = frappe.get_doc({'doctype': 'Employee Checkin', 'employee': employee.name,
                'time': f'2026-09-{day} ' + clock, 'log_type': kind})
            punch.insert()
            owned.append((punch.doctype, punch.name))

    def source(day, hours, rest_start, rest_end):
        source_type = retro.DT if MIXED and day == 15 else 'Overtime Authorization'
        if source_type == retro.DT:
            doc = frappe.get_doc({'doctype': retro.DT, 'employee': employee.name, 'work_date': f'2026-09-{day}',
                'authorization_start': f'2026-09-{day} 18:00:00', 'authorization_end': f'2026-09-{day} {18+hours}:00:00',
                'maximum_hours': hours, 'reason': prefix, 'exception_justification': prefix + ' synthetic historical exception',
                'planned_settlement': 'Compensatory Rest', 'settlement_payroll_date': '2026-09-20',
                'reconciliation_engine': retro.ENGINE})
            doc.insert()
            owned.append((doc.doctype, doc.name))
            doc.submit()
            name = doc.name
            assert doc.evidence_status == 'Verified', doc.evidence_issues
        else:
            call = frappe.copy_doc(frappe.get_doc('Overtime Work Call', 'CONV-HE-2026-00004-1'))
            call.name, call.docstatus = None, 0
            call.company, call.from_date, call.to_date = employee.company, f'2026-09-{day}', f'2026-09-{day}'
            call.planned_settlement, call.automation_mode = 'Compensatory Rest', 'Verified Checkins'
            call.evidence_auto_settle = 1
            call.set('employees', [])
            call.append('employees', {'employee': employee.name})
            call.set('dates', [])
            call.append('dates', {'work_date': f'2026-09-{day}', 'start_time': '18:00:00',
                'end_time': f'{18+hours}:00:00', 'requested_hours': hours})
            call.insert()
            owned.append((call.doctype, call.name))
            call.submit()
            name = frappe.db.get_value('Overtime Authorization', {'overtime_work_call': call.name}, 'name')
            owned.append(('Overtime Authorization', name))
            result = evidence.process_authorization(name)
            assert result == 'Verified', (result, frappe.db.get_value('Overtime Authorization', name, 'evidence_issues'))
        election = frappe.get_doc({'doctype': 'Overtime Settlement Election', ('retroactive_adjustment' if source_type == retro.DT else 'authorization'): name,
            'choice': 'Compensatory Rest', 'employee_reference': prefix,
            'planned_start': '2026-09-22 ' + rest_start, 'planned_end': '2026-09-22 ' + rest_end})
        election.insert()
        owned.append((election.doctype, election.name))
        rest.approve_election(election.name)
        return {'auth': name, 'election': election.name, 'source_type': source_type}

    a = source(14, 2, '08:00:00', '10:00:00')
    b = source(15, 3, '10:00:00', '13:00:00')
    frappe.db.commit()
    results = race([a, b], ['settle', 'settle'])
    assert [r['status'] for r in results] == ['Frozen', 'Frozen'], results
    totals = bank._get_bank_totals(employee.name, employee.company, leave_type, period.name)
    assert totals == {'active_hours': 5, 'effective_days': .5}, totals
    credits = frappe.get_all('Overtime Compensatory Credit', filters={'employee': employee.name, 'docstatus': 1},
        fields=['name', 'overtime_authorization', 'banked_hours', 'credited_days', 'residual_hours_after', 'leave_allocation'])
    assert len(credits) == 2 and sum(c.credited_days for c in credits) == .5, credits
    first = next(c for c in credits if c.overtime_authorization == a['auth'])
    assert first.credited_days == 0 and not first.leave_allocation and first.residual_hours_after == 2, first
    allocations = frappe.get_all('Leave Allocation', filters={'employee': employee.name, 'docstatus': 1}, fields=['name','new_leaves_allocated'])
    assert len(allocations) == 1 and allocations[0].new_leaves_allocated == .5, allocations
    entries = frappe.get_all('Leave Ledger Entry', filters={'employee': employee.name,'docstatus':1,'transaction_type':'Leave Allocation'}, pluck='leaves')
    assert sum(entries) == .5, entries
    print('Concurrent residual credits: 2h + 3h = 0.5 day plus 1h; one allocation and correct ledger', flush=True)

    leave = frappe.get_doc({'doctype':'Leave Application','employee':employee.name,'company':employee.company,
        'leave_type':leave_type,'from_date':'2026-09-22','to_date':'2026-09-22','half_day':1,'half_day_date':'2026-09-22',
        'posting_date':'2026-09-20','status':'Approved','leave_approver':'Administrator','follow_via_email':0,'description':prefix})
    leave.insert()
    owned.append((leave.doctype,leave.name))
    competing = frappe.copy_doc(leave)
    competing.from_date = competing.to_date = competing.half_day_date = '2026-09-23'
    competing.insert()
    owned.append((competing.doctype,competing.name))
    frappe.db.commit()
    results = race([{**a,'leave':leave.name},{**a,'leave':competing.name}], ['submit_leave','submit_leave'])
    assert [r['status'] for r in results] == ['Leave Submitted','Rejected'], results
    leave.reload()
    assert leave.docstatus == 1 and frappe.db.get_value('Leave Application',competing.name,'docstatus') == 0
    assert leave.total_leave_days == .5
    print('Two native leave submissions cannot spend the same half-day balance twice', flush=True)
    a['leave'] = b['leave'] = leave.name
    frappe.db.commit()
    results = race([a,b], ['link','link'])
    assert [r['status'] for r in results] == ['Scheduled','Rejected'], results
    assert frappe.db.count('Overtime Settlement Election', {'leave_application': leave.name, 'docstatus':1}) == 1
    print('Concurrent claims cannot overbook one half-day leave', flush=True)

    results = race([a,a], ['enjoy','cancel_leave'])
    assert [r['status'] for r in results] == ['Enjoyed','Rejected'], results
    assert frappe.db.get_value('Leave Application', leave.name, 'docstatus') == 1
    assert frappe.db.get_value('Overtime Settlement Election', a['election'], 'status') == 'Enjoyed'
    rest.revoke_enjoyment(a['election'], prefix + ' synthetic correction before reversal')
    frappe.db.commit()
    print('Concurrent enjoyment confirmation prevents cancellation of its backing leave', flush=True)

    # Neither a cancellation nor its released election may survive a failed reversal.
    doc = frappe.get_doc('Overtime Authorization', a['auth'])
    try:
        doc.cancel()
    except frappe.ValidationError:
        frappe.db.rollback()
    else:
        raise AssertionError('Consumed residual credit was reversed')
    assert frappe.db.get_value('Overtime Authorization', a['auth'], 'docstatus') == 1
    assert frappe.db.get_value('Overtime Settlement Election', a['election'], 'status') == 'Scheduled'
    assert bank._get_bank_totals(employee.name, employee.company, leave_type, period.name) == totals
    print('Used-leave reversal rejection rolls back source, election and bank', flush=True)

    results = race([a,a], ['cancel_leave','cancel'])
    assert [r['status'] for r in results] == ['Leave Cancelled','Cancelled'], results
    assert bank._get_bank_totals(employee.name, employee.company, leave_type, period.name) == {'active_hours':3,'effective_days':0}
    allocation = frappe.get_doc('Leave Allocation', allocations[0].name)
    assert allocation.docstatus == 1 and allocation.new_leaves_allocated == 0
    entries = frappe.get_all('Leave Ledger Entry', filters={'employee':employee.name,'docstatus':1,'transaction_type':'Leave Allocation'}, pluck='leaves')
    assert sum(entries) == 0, entries
    assert frappe.db.get_value('Overtime Compensatory Credit', first.name, 'docstatus') == 2
    assert frappe.db.get_value('Overtime Compensatory Credit', first.name, 'reversed_days') == .5
    assert frappe.db.get_value('Overtime Settlement Election', a['election'], 'status') == 'Cancelled'
    assert not frappe.db.count('Additional Salary', {'employee':employee.name})
    if MIXED:
        results = race([b,b], ['link','cancel'])
        assert [r['status'] for r in results] == ['Rejected','Cancelled'], results
        assert frappe.db.get_value(retro.DT, b['auth'], 'docstatus') == 2
        assert frappe.db.get_value('Overtime Settlement Election', b['election'], 'status') == 'Cancelled'
        assert bank._get_bank_totals(employee.name,employee.company,leave_type,period.name) == {'active_hours':0,'effective_days':0}
        print('MIXED_SOURCE_BANK_PASS: native Authorization and Retroactive claims share one bank; native cancellations release both claims and leave zero balance', flush=True)
    else:
        same_call = {**b, 'mutex_doctype': 'Overtime Work Call'}
        results = race([same_call,same_call], ['settle','cancel'])
        assert [r['status'] for r in results] == ['Frozen','Cancelled'], results
        assert frappe.db.get_value('Overtime Authorization', b['auth'], 'docstatus') == 2
        assert bank._get_bank_totals(employee.name,employee.company,leave_type,period.name) == {'active_hours':0,'effective_days':0}
        print('Native authorization cancellation serializes with its settlement service on the same Work Call', flush=True)
    print('REST_BANK_RACES_PASS: intermediate residual reversal preserved three hours; final source cancellation leaves zero bank balance')
finally:
    for proc in processes:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    for barrier in barriers:
        for path in Path('/tmp').glob(Path(barrier).name + '*'):
            path.unlink()
    frappe.db.rollback()
    for dt in ['Overtime Reconciliation Run','Overtime Settlement Election','Overtime Compensatory Credit',
            'Leave Allocation','Leave Application','Leave Ledger Entry','Attendance','Additional Salary']:
        owned.extend((dt,name) for name in frappe.get_all(dt, filters={'employee':employee_name}, pluck='name'))
    for dt,name in reversed(list(dict.fromkeys(owned))):
        for field in frappe.get_meta(dt).get_table_fields():
            frappe.db.delete(field.options, {'parent':name,'parenttype':dt})
        for audit,filters in [('Version',{'ref_doctype':dt,'docname':name}),
                ('Comment',{'reference_doctype':dt,'reference_name':name}),('DocShare',{'share_doctype':dt,'share_name':name})]:
            frappe.db.delete(audit,filters)
        frappe.db.delete(dt,{'name':name})
    frappe.db.commit()
    after = {dt:frappe.db.count(dt) for dt in types}
    assert baseline == after, (baseline,after)
    for dt, values in settings_before.items():
        assert values == frappe.db.get_singles_dict(dt), dt
    print('REST_BANK_RACES_CLEANUP', json.dumps(after))
    frappe.db.rollback()
    frappe.destroy()
