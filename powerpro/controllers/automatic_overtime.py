"""Opt-in, per-authorization settlement and auditable HR exceptions.

Lock order: Work Call -> Employee -> Authorization. The scheduler commits one
source at a time. An exception's financial reversal/replacement is one savepoint;
failed reversals retain the original financial evidence and a pending audit.
"""
import hashlib
import json
from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import cint, flt, get_datetime, getdate, now_datetime

from powerpro.controllers.overtime import _reconcile, _reconciliation_rows
from powerpro.payroll_rules.manual_overtime import normalize_intervals, verification_roles
from powerpro.payroll_rules.overtime_work_call import derive_reconciliation_snapshot

AUTH = 'Overtime Authorization'
CALL = 'Overtime Work Call'
EXCEPTION = 'Overtime Attendance Exception'
FINAL = {'Created', 'Payroll Submitted', 'Paid', 'Credited'}
ACTIONS = {'Mark Absent', 'Correct Worked Hours', 'Cancel Participation'}
AUTO_FIELDS = ('auto_enrolled', 'auto_status', 'auto_payroll_date', 'auto_attempts',
               'auto_last_attempt', 'auto_retry_after', 'auto_error', 'attendance_state',
               'presumed_hours', 'presumed_on', 'attendance_exception')
CALL_FIELDS = ('automatic_settlement_enabled', 'auto_payroll_date_policy',
               'automatic_enrolled_by', 'automatic_enrolled_on', 'automatic_status',
               'presumed_hours', 'automatic_settled_count', 'automatic_blocked_count',
               'correction_pending_count')
HOUR_FIELDS = ('verified_hours', 'regular_35_hours', 'regular_100_hours', 'holiday_100_hours',
               'weekly_rest_hours', 'night_hours', 'unapproved_hours', 'missing_hours')


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _settings():
    return frappe.get_single('DGII Payroll Settings')


def validate_settings(settings):
    if not settings.get('enable_automatic_overtime_settlement'):
        return
    if not settings.enable_overtime_authorization or not settings.enable_overtime_settlement:
        frappe.throw(_('Enable Overtime Authorization and Overtime Settlement first.'))
    roles = verification_roles(settings.get('overtime_exception_roles'))
    if not roles:
        frappe.throw(_('Select at least one Overtime Attendance Exception Role.'))
    for role in roles:
        if role in {'All', 'Guest'} or not frappe.db.get_value('Role', role, 'desk_access') or frappe.db.get_value('Role', role, 'disabled'):
            frappe.throw(_('Attendance exceptions require an enabled Desk role: {0}').format(role))
    if settings.get('overtime_auto_payroll_date_policy') not in {'Work Date', 'Month End', 'Work Call Date'}:
        frappe.throw(_('Choose an Automatic Cash Payroll Date Policy.'))


def protect_fields(doc):
    before = doc.get_doc_before_save()
    from powerpro.payroll_rules.overtime_evidence import EVIDENCE_FIELDS
    fields = (CALL_FIELDS + ('evidence_reconciliation_enabled',)) if doc.doctype == CALL else AUTO_FIELDS + EVIDENCE_FIELDS
    if before:
        changed = any((before.get(f) or '') != (doc.get(f) or '') for f in fields)
    else:
        changed = any(doc.get(f) for f in fields)
    if changed:
        frappe.throw(_('Automatic settlement audit fields are managed by the Work Call service.'))
    if doc.doctype == AUTH and (doc.get('auto_enrolled') or doc.get('evidence_enrolled') or doc.get('reconciliation_source') in {'Presumed Attendance', 'HR Exception'}):
        from powerpro.controllers.manual_overtime import AUDIT_FIELDS
        if not before or any(before.get(f) != doc.get(f) for f in AUDIT_FIELDS):
            frappe.throw(_('Use Attendance Exceptions on the Work Call to change this attendance.'))


def prepare_submission(call):
    if call.get('automation_mode') == 'Verified Checkins':
        from powerpro.controllers.checkin_overtime import validate_enrollment
        validate_enrollment(call)
        return
    settings = _settings()
    if not cint(settings.get('enable_automatic_overtime_settlement')) or call.get('automation_mode') == 'Manual':
        return
    validate_settings(settings)
    _payroll_date(call, call.to_date, settings.overtime_auto_payroll_date_policy)


def enroll_on_submit(call):
    if call.get('automation_mode') == 'Verified Checkins':
        from powerpro.controllers.checkin_overtime import enroll_call
        enroll_call(call)
        return
    settings = _settings()
    if cint(settings.get('enable_automatic_overtime_settlement')) and call.get('automation_mode') != 'Manual':
        _enroll(call, settings)


def _payroll_date(call, work_date, policy):
    if call.planned_settlement != 'Cash':
        return None
    if policy == 'Work Date':
        return getdate(work_date)
    if policy == 'Month End':
        import calendar
        date = getdate(work_date)
        return date.replace(day=calendar.monthrange(date.year, date.month)[1])
    if policy != 'Work Call Date' or not call.get('automatic_payroll_date') or getdate(call.automatic_payroll_date) < getdate(work_date):
        frappe.throw(_('Automatic Cash Payroll Date must be on or after every work date.'))
    return getdate(call.automatic_payroll_date)


def _enroll(call, settings):
    if call.docstatus != 1:
        frappe.throw(_('Submit the Work Call before enrolling it.'))
    if call.get('automatic_settlement_enabled'):
        return
    names = frappe.get_all(AUTH, filters={'overtime_work_call': call.name, 'docstatus': 1}, pluck='name')
    if len(names) != cint(call.authorization_count):
        frappe.throw(_('The Work Call authorization set is incomplete.'))
    policy = settings.get('overtime_auto_payroll_date_policy') or 'Work Date'
    for name in names:
        doc, _call = _lock(name)
        if doc.get('settlement_status') in FINAL or doc.get('reconciled_on'):
            frappe.throw(_('Only a Work Call with entirely unsettled, unreconciled authorizations can be enrolled.'))
        doc.db_set({'auto_enrolled': 1, 'auto_status': 'Queued', 'attendance_state': 'Presumed Present',
                    'auto_retry_after': now_datetime(), 'auto_payroll_date': _payroll_date(call, doc.work_date, policy)})
    call.db_set({'automatic_settlement_enabled': 1, 'auto_payroll_date_policy': policy,
                 'automatic_enrolled_by': frappe.session.user, 'automatic_enrolled_on': now_datetime()})
    call.add_comment('Info', _('Automatic settlement enrolled explicitly; attendance is presumed. Cash payroll date policy: {0}.').format(policy))
    _sync(call)


def _allowed(doc, settings=None):
    settings = settings or _settings()
    return (frappe.session.user == doc.get('approver') or bool(
        verification_roles(settings.get('overtime_exception_roles')).intersection(frappe.get_roles(frappe.session.user))))


def _access(doc):
    doc.check_permission('read')
    if not _allowed(doc):
        frappe.throw(_('Your role is not permitted to record this attendance exception.'), frappe.PermissionError)


def _lock(name):
    ref = frappe.db.get_value(AUTH, name, ['overtime_work_call', 'employee'], as_dict=True)
    if not ref or not ref.overtime_work_call:
        frappe.throw(_('Select a Work Call authorization.'))
    call = frappe.get_doc(CALL, ref.overtime_work_call, for_update=True)
    frappe.db.get_value('Employee', ref.employee, 'name', for_update=True)
    doc = frappe.get_doc(AUTH, name, for_update=True)
    if doc.employee != ref.employee or doc.overtime_work_call != call.name:
        frappe.throw(_('Authorization changed. Reload the Work Call.'))
    if doc.docstatus != 1 or doc.status != 'Approved' or call.docstatus != 1:
        frappe.throw(_('The Work Call and authorization must remain submitted and approved.'))
    return doc, call


@frappe.whitelist()
def get_work_call_status(work_call):
    call = frappe.get_doc(CALL, work_call)
    call.check_permission('read')
    settings = _settings()
    rows = frappe.get_all(AUTH, filters={'overtime_work_call': call.name, 'docstatus': 1},
        fields=['name', 'employee_name', 'employee', 'work_date', 'authorization_start', 'authorization_end',
                'maximum_hours', 'approver', 'auto_enrolled', 'auto_status', 'attendance_state', 'verified_hours',
                'presumed_hours', 'settlement_status', 'auto_error', 'attendance_exception'],
        order_by='work_date asc, employee_name asc')
    for row in rows:
        row['can_correct'] = _allowed(row, settings)
    return {'rows': rows, 'payroll_date_policy': call.get('auto_payroll_date_policy') or settings.get('overtime_auto_payroll_date_policy'),
            'payroll_date': call.get('automatic_payroll_date'), 'planned_settlement': call.planned_settlement, 'enabled': cint(settings.get('enable_automatic_overtime_settlement')),
            'enrolled': cint(call.get('automatic_settlement_enabled')),
            'can_enroll': bool(verification_roles(settings.get('overtime_exception_roles')).intersection(frappe.get_roles(frappe.session.user)))}


@frappe.whitelist(methods=['POST'])
def enroll_work_call(work_call, modified):
    call = frappe.get_doc(CALL, work_call, for_update=True)
    call.check_permission('read')
    settings = _settings()
    if not cint(settings.get('enable_automatic_overtime_settlement')) or not verification_roles(settings.get('overtime_exception_roles')).intersection(frappe.get_roles(frappe.session.user)):
        frappe.throw(_('Automatic settlement is disabled or your role cannot enroll Work Calls.'), frappe.PermissionError)
    if str(call.modified) != modified:
        frappe.throw(_('The Work Call changed. Reload it before enrollment.'))
    _enroll(call, settings)
    return get_work_call_status(call.name)


def _freeze_attendance(doc, intervals=None):
    presumed = intervals is None
    intervals = intervals if intervals is not None else [{'start': str(doc.authorization_start), 'end': str(doc.authorization_end)}]
    result = _reconcile(doc, include_weekly_context=True, manual_intervals=intervals, for_update=True)
    snapshot = derive_reconciliation_snapshot(authorization_start=doc.authorization_start,
        authorization_end=doc.authorization_end, maximum_hours=doc.maximum_hours,
        reconciliation=result, evaluation_time=now_datetime(), evidence_source='Manual Verification')
    hours = flt(snapshot['verified_hours'])
    if hours <= 0:
        frappe.throw(_('The approved interval contains no eligible overtime hours.'))
    values = {**snapshot, 'reconciliation_source': 'Presumed Attendance' if presumed else 'HR Exception',
              'presumed_hours': hours if presumed else 0, 'verified_hours': 0 if presumed else hours,
              'reconciled_on': now_datetime(), 'reconciled_by': frappe.session.user,
              'reconciliation_intervals': _json(result['intervals']),
              'reconciliation_warnings': '\n'.join(result['warnings']),
              'unapproved_intervals': _json(result['unapproved_intervals']), 'source_checkins': '[]'}
    if presumed:
        values.update(reconciliation_status='Presumed', presumed_on=now_datetime(), adherence_percent=0,
                      actual_start=None, actual_end=None)
    doc.db_set(values)


def _check_weekly_dependencies(doc, *, correction=False):
    # Earlier changes cannot silently invalidate later frozen overtime bands.
    if doc.day_classification != 'Regular Workday':
        return
    date = getdate(doc.work_date)
    week_start = date - timedelta(days=date.weekday())
    rows = _reconciliation_rows(AUTH, for_update=True, filters={'employee': doc.employee, 'docstatus': 1,
        'work_date': ['between', [week_start, week_start + timedelta(days=6)]]},
        fields=['name', 'authorization_start', 'auto_enrolled', 'auto_status', 'regular_35_hours', 'regular_100_hours'])
    blockers = []
    for row in rows:
        if row.name == doc.name:
            continue
        if not correction and row.auto_enrolled and get_datetime(row.authorization_start) < get_datetime(doc.authorization_start) and row.auto_status not in {'Settled', 'Excluded', 'Cancelled'}:
            blockers.append(row.name)
        if (correction or not doc.get('reconciled_on')) and get_datetime(row.authorization_start) > get_datetime(doc.authorization_start) and flt(row.regular_35_hours) + flt(row.regular_100_hours) > 0:
            blockers.append(row.name)
    if blockers:
        frappe.throw(_('Review dependent overtime authorizations first: {0}').format(', '.join(blockers)))


def process_authorization(name):
    """Internal transaction unit. Caller owns commit/rollback; never exposed as RPC."""
    doc, call = _lock(name)
    settings = _settings()
    if not (cint(settings.get('enable_automatic_overtime_settlement')) and cint(settings.enable_overtime_settlement)):
        return 'Paused'
    if not doc.get('auto_enrolled') or doc.get('auto_status') not in {'Queued', 'Blocked'}:
        return doc.get('auto_status')
    if get_datetime(doc.authorization_end) > now_datetime():
        return 'Queued'
    if doc.get('settlement_status') in FINAL:
        doc.db_set({'auto_status': 'Settled', 'auto_error': None})
        _sync(call)
        return 'Settled'
    _check_weekly_dependencies(doc)
    if doc.get('attendance_state') in {'Mark Absent', 'Cancel Participation'}:
        doc.db_set('auto_status', 'Excluded')
    else:
        if doc.get('attendance_state') != 'Correct Worked Hours':
            _freeze_attendance(doc)
        from powerpro.controllers.overtime_settlement import _settle_authorization
        _settle_authorization(doc, payroll_date=doc.auto_payroll_date, settings=settings)
        doc.db_set({'auto_status': 'Settled', 'auto_error': None, 'auto_retry_after': None,
                    'auto_attempts': cint(doc.auto_attempts) + 1, 'auto_last_attempt': now_datetime()})
    _sync(call)
    return doc.auto_status


def scheduled_process_due():
    if not cint(_settings().get('enable_automatic_overtime_settlement')):
        return
    names = frappe.get_all(AUTH, filters={'auto_enrolled': 1, 'docstatus': 1,
        'auto_status': ['in', ['Queued', 'Blocked']], 'authorization_end': ['<=', now_datetime()],
        'auto_retry_after': ['<=', now_datetime()]},
        fields=['name', 'auto_retry_after'], order_by='authorization_start asc, name asc', limit=100)
    for row in names:
        if row.auto_retry_after and get_datetime(row.auto_retry_after) > now_datetime():
            continue
        try:
            process_authorization(row.name)
            frappe.db.commit()
        except Exception as exc:
            frappe.db.rollback()
            try:
                doc, call = _lock(row.name)
                if doc.auto_status in {'Queued', 'Blocked'}:
                    doc.db_set({'auto_status': 'Blocked', 'auto_error': str(exc)[:2000],
                        'auto_attempts': cint(doc.auto_attempts) + 1, 'auto_last_attempt': now_datetime(),
                        'auto_retry_after': now_datetime() + timedelta(minutes=10)})
                    _sync(call)
                frappe.db.commit()
            except Exception:
                frappe.db.rollback()
                frappe.log_error(title='Automatic overtime processing failed')


def _exception_input(doc, action, reason, intervals):
    if action not in ACTIONS or not isinstance(reason, str) or not reason.strip() or len(reason) > 2000:
        frappe.throw(_('Choose an attendance action and enter a reason of 1 to 2000 characters.'))
    if doc.get('auto_status') == 'Correction Pending':
        frappe.throw(_('Resolve or retry the pending attendance correction first.'))
    if not doc.get('auto_enrolled'):
        frappe.throw(_('Enroll this Work Call before using automatic attendance exceptions.'))
    rows = []
    if action == 'Correct Worked Hours':
        try:
            rows = normalize_intervals(json.loads(intervals) if isinstance(intervals, str) else intervals,
                authorization_start=doc.authorization_start, authorization_end=doc.authorization_end, now=now_datetime())
        except (TypeError, ValueError) as exc:
            frappe.throw(str(exc))
    return {'authorization': doc.name, 'modified': str(doc.modified), 'action': action,
            'reason': reason.strip(), 'intervals': rows, 'settlement_status': doc.settlement_status,
            'settlement_references': doc.get('settlement_references')}


@frappe.whitelist()
def preview_attendance_exception(authorization, action, reason, intervals=None):
    doc = frappe.get_doc(AUTH, authorization)
    _access(doc)
    data = _exception_input(doc, action, reason, intervals)
    data['token'] = hashlib.sha256(_json(data).encode()).hexdigest()
    return data


@frappe.whitelist(methods=['POST'])
def record_attendance_exception(authorization, action, reason, token, intervals=None):
    doc, call = _lock(authorization)
    _access(doc)
    # A confirmation retry returns the same immutable audit; it never reverses twice.
    existing = frappe.db.get_value(EXCEPTION, {'request_key': token}, 'name', for_update=True)
    if existing:
        return {'exception': existing, 'status': frappe.db.get_value(EXCEPTION, existing, 'status')}
    preview = _exception_input(doc, action, reason, intervals)
    if not token or hashlib.sha256(_json(preview).encode()).hexdigest() != token:
        frappe.throw(_('Attendance changed. Review a new exception preview.'))
    event = frappe.new_doc(EXCEPTION)
    event.update({'authorization': doc.name, 'work_call': call.name, 'employee': doc.employee,
        'work_date': doc.work_date, 'action': action, 'reason': preview['reason'],
        'worked_intervals': _json(preview['intervals']), 'status': 'Correction Pending',
        'recorded_by': frappe.session.user, 'recorded_on': now_datetime(), 'request_key': token,
        'before_snapshot': _snapshot(doc)})
    # Service-owned immutable audit: generic document saves are deliberately rejected.
    event.name = frappe.generate_hash(length=12)
    event.db_insert()
    return _apply_exception(doc, call, event)


@frappe.whitelist(methods=['POST'])
def retry_attendance_exception(authorization):
    doc, call = _lock(authorization)
    _access(doc)
    if doc.auto_status != 'Correction Pending' or not doc.attendance_exception:
        frappe.throw(_('This authorization has no pending attendance correction.'))
    event = frappe.get_doc(EXCEPTION, doc.attendance_exception, for_update=True)
    return _apply_exception(doc, call, event)


def _apply_exception(doc, call, event):
    frappe.db.savepoint('overtime_exception_financial')
    try:
        _check_weekly_dependencies(doc, correction=True)
        _reverse_outputs(doc, event)
        values = {f: 0 for f in HOUR_FIELDS}
        values.update(presumed_hours=0, settlement_status='Pending', settlement_amount=0,
            compensatory_hours=0, compensatory_days=0, compensatory_residual_hours=0,
            settlement_references=None, settlement_breakdown=None, compensatory_credit=None,
            leave_allocation=None, settlement_salary_slip=None, settlement_method=None,
            attendance_state=event.action, attendance_exception=event.name,
            auto_error=None, auto_retry_after=None)
        doc.db_set(values)
        if event.action == 'Correct Worked Hours':
            _freeze_attendance(doc, json.loads(event.worked_intervals))
            doc.db_set('auto_status', 'Queued')
            # Replacement is atomic with reversal even when global scheduling is paused.
            from powerpro.controllers.overtime_settlement import _settle_authorization
            _settle_authorization(doc, payroll_date=doc.auto_payroll_date, settings=_settings())
            doc.db_set('auto_status', 'Settled')
        else:
            doc.db_set({'auto_status': 'Excluded', 'reconciliation_status': 'Absent',
                'reconciliation_source': 'HR Exception', 'reconciled_by': frappe.session.user,
                'reconciled_on': now_datetime(), 'adherence_percent': 0,
                'actual_start': None, 'actual_end': None, 'reconciliation_intervals': '[]'})
        event.db_set({'status': 'Applied', 'after_snapshot': _snapshot(frappe.get_doc(AUTH, doc.name, for_update=True)),
            'blockers': None, 'resolved_by': frappe.session.user, 'resolved_on': now_datetime()})
    except Exception as exc:
        frappe.local.message_log = []
        frappe.db.rollback(save_point='overtime_exception_financial')
        doc = frappe.get_doc(AUTH, doc.name, for_update=True)
        blockers = _blocking_documents(doc)
        event.db_set({'status': 'Correction Pending', 'blockers': _json({'reason': str(exc), 'documents': blockers})})
        doc.db_set({'attendance_state': event.action, 'attendance_exception': event.name,
            'auto_status': 'Correction Pending', 'auto_error': str(exc)[:2000]})
    call.add_comment('Info', _('Attendance exception {0} recorded for {1}: {2}.').format(event.name, doc.name, event.status))
    _sync(call)
    return {'exception': event.name, 'status': event.status, 'blockers': event.get('blockers')}


def _reverse_outputs(doc, event):
    if doc.get('settlement_status') not in FINAL:
        return
    if doc.get('settlement_method') == 'Cash':
        from powerpro.controllers.overtime_cash_settlement import before_cancel_adjustment, _get_linked_additional_salaries
        before_cancel_adjustment(doc)
        names = _get_linked_additional_salaries(doc, docstatus=1, for_update=True)
        previous = frappe.flags.get('overtime_exception_reversal')
        frappe.flags.overtime_exception_reversal = doc.name
        try:
            for name in names:
                salary = frappe.get_doc('Additional Salary', name, for_update=True)
                salary.flags.ignore_permissions = True
                salary.cancel()
        finally:
            frappe.flags.overtime_exception_reversal = previous
    elif doc.get('settlement_method') == 'Compensatory Rest':
        from powerpro.controllers.overtime_compensatory_settlement import reverse_compensatory_credit
        # Detach only this source's forward link inside the reversal savepoint.
        # The credit keeps its authorization link and immutable original audit.
        frappe.db.set_value(AUTH, doc.name, 'compensatory_credit', None, update_modified=False)
        reverse_compensatory_credit(doc, reason='Attendance exception ' + event.name + ': ' + event.reason)


def _blocking_documents(doc):
    from powerpro.controllers.overtime_cash_settlement import _get_linked_additional_salaries, _get_submitted_salary_slips
    refs = _get_linked_additional_salaries(doc, docstatus=1, for_update=True)
    links = [{'doctype': 'Salary Slip', 'name': n} for n in _get_submitted_salary_slips(refs, for_update=True)]
    if doc.get('leave_allocation'):
        links.append({'doctype': 'Leave Allocation', 'name': doc.leave_allocation})
        allocation = frappe.get_doc('Leave Allocation', doc.leave_allocation, for_update=True)
        names = _reconciliation_rows('Leave Application', for_update=True, filters={
            'employee': doc.employee, 'leave_type': allocation.leave_type, 'docstatus': 1,
            'from_date': ['<=', allocation.to_date], 'to_date': ['>=', allocation.from_date]}, pluck='name')
        links.extend({'doctype': 'Leave Application', 'name': n} for n in names)
    return links


def _snapshot(doc):
    keys = (*AUTO_FIELDS, *HOUR_FIELDS, 'reconciliation_source', 'reconciliation_status',
        'settlement_status', 'settlement_method', 'settlement_references', 'settlement_breakdown',
        'settlement_amount', 'settlement_salary_slip', 'compensatory_credit', 'leave_allocation')
    return _json({key: doc.get(key) for key in keys})


def _sync(call):
    rows = _reconciliation_rows(AUTH, for_update=True, filters={'overtime_work_call': call.name, 'docstatus': 1},
        fields=['verified_hours', 'presumed_hours', 'auto_status'])
    pending = sum(row.auto_status == 'Correction Pending' for row in rows)
    blocked = sum(row.auto_status == 'Blocked' for row in rows)
    status = 'Correction Pending' if pending else 'Blocked' if blocked else 'Queued' if any(row.auto_status == 'Queued' for row in rows) else 'Complete'
    call.db_set({'automatic_status': status, 'presumed_hours': sum(flt(row.presumed_hours) for row in rows),
        'verified_hours': sum(flt(row.verified_hours) for row in rows), 'automatic_settled_count': sum(row.auto_status == 'Settled' for row in rows),
        'automatic_blocked_count': blocked, 'correction_pending_count': pending})


def lock_payroll_inputs(slip, method=None):
    """Serialize payroll submission/cancellation with overtime corrections."""
    refs = sorted({r.additional_salary for r in slip.get('earnings', []) if r.additional_salary})
    if not refs:
        return
    frappe.db.get_value('Employee', slip.employee, 'name', for_update=True)
    for name in refs:
        salary = frappe.get_doc('Additional Salary', name, for_update=True)
        if salary.ref_doctype == 'Ordinary Night Settlement' and salary.ref_docname:
            source = frappe.get_doc(salary.ref_doctype, salary.ref_docname, for_update=True)
            if method == 'before_submit':
                if salary.docstatus != 1 or source.docstatus != 1:
                    frappe.throw(_('El recargo nocturno vinculado fue cancelado. Actualice esta nómina.'))
                from powerpro.controllers.ordinary_night import validate_fresh
                validate_fresh(source)
            continue
        if salary.ref_doctype != AUTH or not salary.ref_docname:
            continue
        source = frappe.get_doc(AUTH, salary.ref_docname, for_update=True)
        if method == 'before_submit' and (salary.docstatus != 1 or source.docstatus != 1 or source.get('auto_status') == 'Correction Pending'):
            frappe.throw(_('Overtime payroll input {0} was cancelled or has a pending correction. Refresh this Salary Slip.').format(name))


def lock_leave_balance(application, method=None):
    frappe.db.get_value('Employee', application.employee, 'name', for_update=True)
    if method != 'before_submit' or application.status != 'Approved':
        return
    rows = _reconciliation_rows('Leave Allocation', for_update=True, filters={
        'employee': application.employee, 'leave_type': application.leave_type,
        'docstatus': 1, 'powerpro_overtime_managed': 1,
        'from_date': ['<=', application.to_date], 'to_date': ['>=', application.from_date]},
        fields=['name', 'from_date', 'to_date', 'total_leaves_allocated'])
    for allocation in rows:
        used = approved_leave_days(application.employee, application.leave_type, allocation.from_date, allocation.to_date, exclude=application.name)
        if used + flt(application.total_leave_days) > flt(allocation.total_leaves_allocated) + 0.0001:
            frappe.throw(_('The overtime leave balance changed. Refresh this Leave Application.'))


def approved_leave_days(employee, leave_type, start, end, exclude=None):
    rows = _reconciliation_rows('Leave Application', for_update=True, filters={
        'employee': employee, 'leave_type': leave_type, 'docstatus': 1, 'status': 'Approved',
        'from_date': ['<=', end], 'to_date': ['>=', start]}, fields=['name', 'total_leave_days'])
    return sum(flt(row.total_leave_days) for row in rows if row.name != exclude)



@frappe.whitelist()
def get_attendance_exception(authorization):
    doc = frappe.get_doc(AUTH, authorization)
    doc.check_permission('read')
    if not doc.get('attendance_exception'):
        return None
    event = frappe.get_doc(EXCEPTION, doc.attendance_exception)
    return {key: event.get(key) for key in ('name', 'action', 'reason', 'status',
        'recorded_by', 'recorded_on', 'resolved_by', 'resolved_on', 'blockers',
        'before_snapshot', 'after_snapshot')}


def run_dedicated_job():
    """Optional cron entry for a site whose general Frappe scheduler is disabled.

    Run under an OS flock. It executes only this registered job and respects
    feature disablement, maintenance mode and the job's stopped flag.
    """
    if not frappe.conf.maintenance_mode and cint(_settings().get('enable_checkin_overtime_reconciliation')):
        evidence_job = frappe.get_doc('Scheduled Job Type', 'checkin_overtime.scheduled_reconcile_due')
        if not evidence_job.stopped and evidence_job.get_next_execution() <= now_datetime():
            evidence_job.execute()
    if frappe.conf.maintenance_mode or not cint(_settings().get('enable_automatic_overtime_settlement')):
        return
    job = frappe.get_doc('Scheduled Job Type', 'automatic_overtime.scheduled_process_due')
    if not job.stopped and job.get_next_execution() <= now_datetime():
        job.execute()
