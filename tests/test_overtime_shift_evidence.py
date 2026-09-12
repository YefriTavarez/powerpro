"""Pure shift and HR correction preview tests; never open a site."""
import unittest
from unittest.mock import patch
from test_overtime_calendar import Record, frappe, dt
from powerpro.payroll_rules.overtime_shift_evidence import (
    ALTERNATING, STRICT, FIRST_LAST, EVERY_PAIR, interpret_shift_punches,
    overlay_corrections, summarize_intervals,
)
from powerpro.controllers.overtime_weekly import _corrections


def row(clock, kind='IN', **extra):
    return dict(name=clock+kind, time='2026-09-21T'+clock, log_type=kind,
                shift='DAY', shift_start='2026-09-21T08:00', shift_end='2026-09-21T18:00', **extra)


def policy(mode=ALTERNATING, calc=EVERY_PAIR):
    return {'DAY': dict(determine_check_in_and_check_out=mode, working_hours_calculation_based_on=calc)}


def hours(result):
    return sum((b-a).total_seconds()/3600 for a,b in result['intervals'])


def correction(name='M1', start='18:00', end='22:00', spans=(('18:00','20:00'),), kind='Manual Verification'):
    return dict(name=name, kind=kind, start='2026-09-21T'+start,end='2026-09-21T'+end,
                intervals=[{'start':'2026-09-21T'+a,'end':'2026-09-21T'+b} for a,b in spans])


class ShiftTest(unittest.TestCase):
    def test_alternating_ignores_wrong_directions_with_audit(self):
        x=interpret_shift_punches([row('08:00'),row('12:00'),row('13:00'),row('18:00')],policy())
        self.assertEqual(hours(x),9)
        self.assertIn('direction_reinterpreted',[i['code'] for i in x['issues']])

    def test_first_last_includes_break_every_pair_does_not(self):
        rows=[row('08:00'),row('12:00','OUT'),row('13:00'),row('18:00','OUT')]
        for mode in [ALTERNATING,STRICT]:
            self.assertEqual(hours(interpret_shift_punches(rows,policy(mode,EVERY_PAIR))),9)
            x=interpret_shift_punches(rows,policy(mode,FIRST_LAST))
            self.assertEqual(hours(x),10)
            self.assertIn('first_last_includes_breaks',[i['code'] for i in x['issues']])

    def test_odd_count_is_visible_in_both_native_modes(self):
        rows=[row('08:00'),row('12:00'),row('13:00')]
        for calc,expected in [(EVERY_PAIR,4),(FIRST_LAST,5)]:
            x=interpret_shift_punches(rows,policy(calc=calc))
            self.assertEqual(hours(x),expected)
            self.assertIn('odd_alternating_count',[i['code'] for i in x['issues']])

    def test_strict_repeated_in_matches_native_first_open_pair(self):
        rows=[row('08:00'),row('10:00'),row('12:00','OUT'),row('17:00','OUT')]
        self.assertEqual(hours(interpret_shift_punches(rows,policy(STRICT,EVERY_PAIR))),4)
        self.assertEqual(hours(interpret_shift_punches(rows,policy(STRICT,FIRST_LAST))),9)

    def test_do_not_mix_days_or_shifts(self):
        a=row('08:00');b=row('18:00')
        b.update(shift_start='2026-09-22T08:00',shift_end='2026-09-22T18:00',time='2026-09-22T18:00')
        self.assertEqual(hours(interpret_shift_punches([a,b],policy())),0)

    def test_overnight_session_splits_at_week_boundary(self):
        rows=[row('22:00'),row('06:00','OUT')]
        for r in rows:r.update(shift_start='2026-09-20T22:00',shift_end='2026-09-21T06:00')
        rows[0]['time']='2026-09-20T22:00'
        x=interpret_shift_punches(rows,policy())
        self.assertEqual(hours(x),8)
        summary=summarize_intervals(x['intervals'],week_start='2026-09-21',cutoff='2026-09-21T05:00',threshold=68)
        self.assertEqual((summary['paired_hours'],summary['hours_before_cutoff']),(6,5))
        self.assertFalse(summary['complete'])

    def test_missing_offshift_skipped_and_duplicate_are_not_inferred(self):
        cases=[([row('08:00',offshift=1),row('18:00',offshift=1)],'offshift'),
               ([row('08:00',skip_auto_attendance=1),row('18:00',skip_auto_attendance=1)],'skip_auto_attendance'),
               ([row('08:00'),row('08:00','OUT')],'duplicate_timestamp')]
        for rows,code in cases:
            x=interpret_shift_punches(rows,policy())
            self.assertEqual(hours(x),0);self.assertIn(code,[i['code'] for i in x['issues']])
        rows=[row('08:00'),row('18:00')]
        for r in rows:r['shift_start']=None
        self.assertEqual(hours(interpret_shift_punches(rows,policy())),0)

    def test_policy_permission_gap_does_not_fallback(self):
        x=interpret_shift_punches([row('08:00'),row('18:00')],{})
        self.assertEqual(hours(x),0)
        self.assertEqual(x['issues'][0]['code'],'unavailable_shift_policy')

    def test_duration_and_reversed_strict_first_last_rejected(self):
        x=interpret_shift_punches([row('08:00','OUT'),row('18:00')],policy(STRICT,FIRST_LAST))
        self.assertEqual(hours(x),0)
        self.assertIn('invalid_duration',[i['code'] for i in x['issues']])


class CorrectionTest(unittest.TestCase):
    base=[(dt('2026-09-21T08:00'),dt('2026-09-21T22:00'))]
    def test_replace_window_without_double_count(self):
        x=overlay_corrections(self.base,[correction()])
        self.assertEqual(hours(x),12)
        self.assertEqual(len(x['applied']),1)

    def test_manual_interval_outside_scope_is_clipped(self):
        x=overlay_corrections(self.base,[correction(spans=(('17:00','20:00'),))])
        self.assertEqual(hours(x),12)
        self.assertEqual(x['applied'][0]['intervals'][0]['start'],'2026-09-21T18:00:00')

    def test_absence_removes_only_authorized_window(self):
        x=overlay_corrections(self.base,[correction(kind='Mark Absent',spans=())])
        self.assertEqual(hours(x),10)

    def test_overlapping_corrections_require_review_and_no_arbitrary_priority(self):
        a=correction();b=correction('M2','19:00','23:00',(('19:00','20:00'),))
        x=overlay_corrections(self.base,[a,b])
        self.assertEqual(hours(x),14)
        self.assertEqual(len(x['applied']),0)
        self.assertEqual(len(x['issues']),2)

    def test_empty_or_invalid_manual_does_not_erase_punches(self):
        for c in [correction(spans=()),correction(spans=(('08:00','09:00'),)),correction(spans=(('20:00','19:00'),))]:
            x=overlay_corrections(self.base,[c])
            self.assertEqual(hours(x),14);self.assertTrue(x['issues'])

    def test_union_prevents_double_count_with_adjacent_sessions(self):
        x=summarize_intervals(self.base+self.base,week_start='2026-09-21',cutoff='2026-09-21T18:00',threshold=68)
        self.assertEqual((x['paired_hours'],x['hours_before_cutoff']),(14,10))


class CorrectionAccessTest(unittest.TestCase):
    def setUp(self):
        self.doc=Record(employee='EMP')
        self.source=Record(name='AUTH',employee='EMP',authorization_start='2026-09-21T18:00',authorization_end='2026-09-21T22:00',
                           reconciliation_source='Manual Verification',reconciled_by='HR',reconciled_on='2026-09-22',
                           manual_worked_intervals='[{"start":"2026-09-21T18:00","end":"2026-09-21T20:00"}]')
        self.event=Record(name='EVENT',authorization='AUTH',employee='EMP',status='Applied',action='Correct Worked Hours',
                          worked_intervals=self.source.manual_worked_intervals,resolved_by='HR',resolved_on='2026-09-22')
    def load(self,allowed=True):
        def query(doctype,**kw):return [self.event] if doctype=='Overtime Attendance Exception' else [self.source]
        with patch.object(frappe,'has_permission',return_value=allowed),patch.object(frappe,'get_list',side_effect=query):
            return _corrections(self.doc,dt('2026-09-21'),dt('2026-09-28'))
    def test_current_manual_requires_audit(self):
        self.assertEqual(len(self.load()[0]),1)
        self.source.reconciled_by=None
        self.assertEqual(self.load()[0],[])
    def test_pending_manual_is_not_applied(self):
        self.source.auto_status='Correction Pending'
        self.assertEqual(self.load()[0],[])
    def test_missing_permission_does_not_read(self):
        with patch.object(frappe,'has_permission',return_value=False),patch.object(frappe,'get_list') as query:
            self.assertEqual(_corrections(self.doc,dt('2026-09-21'),dt('2026-09-28'))[0],[])
            query.assert_not_called()
    def test_only_current_applied_event_matching_employee_and_authorization(self):
        self.source.reconciliation_source='HR Exception';self.source.attendance_exception='EVENT'
        self.assertEqual(self.load()[0][0]['name'],'EVENT')
        for key,value in [('status','Correction Pending'),('employee','OTHER'),('authorization','OTHER'),('resolved_on',None),('action','Cancel Participation')]:
            old=self.event[key];self.event[key]=value
            self.assertEqual(self.load()[0],[],key)
            self.event[key]=old
    def test_no_fallback_to_clipped_reconciliation_for_manual(self):
        self.source.manual_worked_intervals=None
        result,_=self.load()
        x=overlay_corrections([],result)
        self.assertEqual(x['applied'],[])
        self.assertTrue(x['issues'])


if __name__=='__main__':unittest.main()
