"""DEV-only read-only worker proof, never payroll activation or a full pilot."""
import hashlib
import inspect
import marshal
import os
import re
from pathlib import Path
from unittest.mock import patch

import frappe
from frappe.utils import cint

SITE='igcaribe.fortabs.com'
COUNTS=('Employee Checkin','Attendance','Overtime Authorization','Overtime Reconciliation Run',
        'Overtime Pay Policy','Ordinary Night Settlement','Additional Salary','Salary Slip',
        'Leave Allocation','Leave Application','Working Time Incident','Error Log','Version','Notification Log')


def manifest():
    from powerpro.controllers import checkin_overtime,ordinary_night_history
    from powerpro.payroll_rules import ordinary_night,overtime_evidence,overtime_observation_window
    methods=(checkin_overtime.process_authorization,checkin_overtime.scheduled_reconcile_due,
             ordinary_night_history.evaluate,ordinary_night.evaluate_night_work,
             overtime_evidence.evaluate_evidence,overtime_observation_window.normalize_window)
    return {f.__module__+'.'+f.__name__:{
        'loaded_code_sha256':hashlib.sha256(marshal.dumps(f.__code__)).hexdigest(),
        'file_sha256':hashlib.sha256(Path(inspect.getsourcefile(f)).read_bytes()).hexdigest()} for f in methods}


def run_probe(probe_id,expected_manifest):
    if frappe.local.site!=SITE or not frappe.conf.developer_mode or frappe.session.user!='Administrator':
        raise frappe.PermissionError('This diagnostic requires Administrator on the explicit Development site.')
    if not re.fullmatch(r'overtime-dev-probe-[0-9a-f]{32}',str(probe_id)):
        raise ValueError('Invalid probe identifier')
    before={dt:frappe.db.count(dt) for dt in COUNTS}
    sql=frappe.db.sql
    def read_only(query,*args,**kwargs):
        if not str(query).lstrip().lower().startswith(('select','show','describe','explain')):
            raise AssertionError('The probe attempted non-read SQL')
        return sql(query,*args,**kwargs)
    def forbidden(*args,**kwargs):raise AssertionError('The probe attempted a commit or outbound action')
    try:
        with (patch.object(frappe.db,'sql',read_only),patch.object(frappe.db,'commit',forbidden),
              patch.object(frappe,'enqueue',forbidden),patch.object(frappe,'sendmail',forbidden),
              patch.object(frappe,'log_error',forbidden)):
            from powerpro.controllers import checkin_overtime
            from powerpro.payroll_rules.ordinary_night import evaluate_night_work
            from powerpro.payroll_rules.overtime_shift_evidence import ALTERNATING,EVERY_PAIR
            assert not cint(checkin_overtime._settings().get('enable_checkin_overtime_reconciliation')),'New processing must remain disabled'
            loaded=manifest();assert loaded==expected_manifest,'Worker code differs from the dispatch process'
            # The sentinel is not a business source. A paused processor must
            # return before looking up or locking any authorization.
            with patch.object(checkin_overtime,'_lock',side_effect=AssertionError('Paused processor tried to load a source')):
                paused=checkin_overtime.process_authorization(probe_id)
                assert paused=='Paused'
                checkin_overtime.scheduled_reconcile_due()
            context=dict(shift_start='2026-09-14T18:00:00',shift_end='2026-09-15T02:00:00',
                         classification='Regular Workday',holiday_list_covers_work_date=True)
            shift=dict(name='SYNTHETIC',last_sync_of_checkin='2026-09-16T00:00:00',
                       determine_check_in_and_check_out=ALTERNATING,working_hours_calculation_based_on=EVERY_PAIR)
            rows=[dict(name='synthetic-in',time=context['shift_start'],log_type='IN',shift='SYNTHETIC',
                       shift_start=context['shift_start'],shift_end=context['shift_end']),
                  dict(name='synthetic-out',time='2026-09-15T06:00:00',log_type='IN',shift=None)]
            result=evaluate_night_work(rows=rows,shift=shift,context=context,extensions=[],next_windows=[],
                now='2026-09-16T00:00:00',basis='Clock overlap',
                observation_window={'start':context['shift_start'],'end':'2026-09-15T06:00:00'})
            assert result['state']=='Needs Review'
            assert result['worked_intervals']==[{'start':context['shift_start'],'end':'2026-09-15T06:00:00'}]
            assert result['unapproved_intervals']==[{'start':context['shift_end'],'end':'2026-09-15T06:00:00'}]
            assert result['source_checkins'][-1]['log_type']=='IN'
            after={dt:frappe.db.count(dt) for dt in COUNTS};assert before==after
            return dict(ok=True,probe_id=probe_id,site=SITE,pid=os.getpid(),manifest=loaded,
                        paused_result=paused,expanded_night_result=result['state'],original_direction='IN',
                        database_counts_unchanged=True,counts=after,scope='Code loading, disabled guards and synthetic pure calculation only')
    except Exception as exc:
        # Return an explicit negative result instead of creating a business Error
        # Log for a diagnostic failure. Caller must check ok, not just RQ status.
        return dict(ok=False,probe_id=probe_id,site=SITE,pid=os.getpid(),error_type=type(exc).__name__,
                    error=str(exc),scope='Diagnostic failure; no readiness claim')
