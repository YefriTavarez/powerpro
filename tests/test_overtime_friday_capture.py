"""Friday payroll schedule versus HRMS base-window capture; no site access."""
from copy import deepcopy
import unittest
from test_overtime_calendar import context, dt
from powerpro.payroll_rules.overtime_evidence import evaluate_evidence
from powerpro.payroll_rules.overtime_actual_week import collect_weekly_work
from powerpro.payroll_rules.overtime_shift_evidence import ALTERNATING, EVERY_PAIR, captured_window_kind


class FridayCaptureTest(unittest.TestCase):
    def setUp(self):
        self.shift = {'name': 'DAY', 'start_time': '08:00', 'end_time': '18:00',
            'custom_hora_salida_viernes': '17:00', 'last_sync_of_checkin': '2026-09-26T10:00',
            'determine_check_in_and_check_out': ALTERNATING,
            'working_hours_calculation_based_on': EVERY_PAIR,
            'begin_check_in_before_shift_start_time': 60, 'allow_check_out_after_shift_end_time': 60}
        self.rows = [dict(name=str(i), shift='DAY', time='2026-09-25T'+clock, log_type=kind,
            shift_start='2026-09-25T08:00', shift_end='2026-09-25T18:00',
            shift_actual_start='2026-09-25T07:00', shift_actual_end='2026-09-25T19:00')
            for i, (clock, kind) in enumerate([('08:00','IN'),('12:00','OUT'),('13:00','IN'),('18:27','OUT')])]
        self.ctx = context('2026-09-25', end='17:00')

    def evaluate(self, shift=None):
        return evaluate_evidence(authorization={'shift':'DAY','start':'2026-09-25T17:00',
            'end':'2026-09-25T18:00','maximum_hours':1}, rows=self.rows,
            shift=shift or self.shift, contexts=[self.ctx], next_windows=[], now='2026-09-26T10:00')

    def test_friday_base_capture_retains_whole_session_and_overrun(self):
        original = deepcopy(self.rows)
        result = self.evaluate()
        self.assertEqual(result['state'], 'Needs Review')
        self.assertEqual(result['snapshot']['verified_hours'], 1)
        self.assertEqual(result['snapshot']['actual_start'], dt('2026-09-25T17:00'))
        self.assertEqual(result['calculation']['unapproved_hours'], .45)
        self.assertEqual(len(result['worked_intervals']), 2)
        self.assertEqual(len(result['interpretations']), 4)
        self.assertTrue(all(r['group']=='configured_friday_schedule' for r in result['interpretations']))
        self.assertEqual(self.rows, original)
        self.assertEqual(result['source_checkins'], original)

    def test_exact_friday_exit_verifies_one_hour_not_zero(self):
        self.rows[-1]['time']='2026-09-25T18:00'
        result=self.evaluate()
        self.assertEqual(result['state'], 'Verified')
        self.assertEqual(result['snapshot']['verified_hours'], 1)

    def test_without_configured_friday_mismatch_stays_unmatched(self):
        shift=dict(self.shift);shift.pop('custom_hora_salida_viernes')
        self.assertNotIn('snapshot', self.evaluate(shift))

    def test_unrelated_shift_or_captured_window_is_not_accepted(self):
        row=self.rows[0]
        for changed in [dict(row,shift='OTHER'),dict(row,shift_end='2026-09-25T16:00'),
                        dict(row,shift_start='2026-09-25T09:00')]:
            self.assertIsNone(captured_window_kind(changed,'DAY',self.ctx['shift_start'],self.ctx['shift_end'],self.shift))
        self.assertIsNone(captured_window_kind(row,'DAY','2026-09-25T08:00','2026-09-25T16:00',self.shift))

    def test_other_weekday_does_not_inherit_friday_rule(self):
        row={k:v.replace('2026-09-25','2026-09-24') if isinstance(v,str) else v for k,v in self.rows[0].items()}
        self.assertIsNone(captured_window_kind(row,'DAY','2026-09-24T08:00','2026-09-24T17:00',self.shift))

    def test_weekly_coverage_matches_base_capture_without_changing_worked_hours(self):
        result=collect_weekly_work(start='2026-09-21T00:00',cutoff='2026-09-26T00:00',
            rows=self.rows,policies={'DAY':self.shift},schedules=[dict(self.ctx,shift='DAY')],attendances=[])
        self.assertTrue(result['complete'],result['issues'])
        self.assertEqual(result['sessions'][0]['hours'],9.45)
        self.assertEqual(result['intervals'][-1]['end'],'2026-09-25T18:27:00')
        shift=dict(self.shift);shift.pop('custom_hora_salida_viernes')
        result=collect_weekly_work(start='2026-09-21T00:00',cutoff='2026-09-26T00:00',
            rows=self.rows,policies={'DAY':shift},schedules=[dict(self.ctx,shift='DAY')],attendances=[])
        self.assertFalse(result['complete'])

    def test_sync_and_exclusion_guards_still_apply(self):
        shift=dict(self.shift,last_sync_of_checkin=None)
        self.assertEqual(self.evaluate(shift)['state'],'Waiting')
        self.rows[-1]['skip_auto_attendance']=1
        self.assertEqual(self.evaluate()['state'],'Needs Review')
        self.assertNotIn('snapshot',self.evaluate())


if __name__ == '__main__':
    unittest.main()
