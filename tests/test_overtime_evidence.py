"""Acceptance of worked-time evidence, no site access."""
import unittest
from test_overtime_calendar import context,dt,legacy
from powerpro.payroll_rules.overtime_evidence import evaluate_evidence
from powerpro.payroll_rules.overtime_shift_evidence import ALTERNATING,STRICT,EVERY_PAIR,FIRST_LAST


def row(clock,kind='IN'):
 return dict(name=clock+kind,time='2026-09-21T'+clock,log_type=kind,shift='DAY',shift_start='2026-09-21T08:00',shift_end='2026-09-21T18:00')

class EvidenceTest(unittest.TestCase):
 def setup_args(self):
  return dict(authorization={'start':'2026-09-21T18:00','end':'2026-09-21T20:00','shift':'DAY','maximum_hours':2},
   rows=[row('08:00'),row('12:00','OUT'),row('13:00'),row('20:00','OUT')],
   shift={'determine_check_in_and_check_out':ALTERNATING,'working_hours_calculation_based_on':EVERY_PAIR,'last_sync_of_checkin':'2026-09-22T08:00',
          'begin_check_in_before_shift_start_time':60,'allow_check_out_after_shift_end_time':60},
   contexts=[context('2026-09-20'),context('2026-09-21')],next_windows=[],now='2026-09-22T10:00')
 def calc(self,**kw):
  args=self.setup_args();args.update(kw);return evaluate_evidence(**args)
 def test_saves_real_overtime_bounds_not_whole_ordinary_shift(self):
  r=self.calc();self.assertEqual(r['state'],'Verified')
  self.assertEqual(r['snapshot']['actual_start'],dt('2026-09-21T18:00'))
  self.assertEqual(r['snapshot']['actual_end'],dt('2026-09-21T20:00'))
  self.assertEqual(r['snapshot']['verified_hours'],2)
 def test_missing_punches_not_absent_or_presumed(self):
  r=self.calc(rows=[]);self.assertEqual(r['state'],'Needs Review');self.assertNotIn('snapshot',r)
 def test_waits_for_complete_sync_even_if_clock_is_past_end(self):
  args=self.setup_args();args['shift']['last_sync_of_checkin']='2026-09-21T19:59'
  r=evaluate_evidence(**args);self.assertEqual(r['state'],'Waiting');self.assertNotIn('snapshot',r)
 def test_future_window_waits(self):self.assertEqual(self.calc(now='2026-09-21T19:00')['state'],'Waiting')
 def test_excluded_punches_cannot_be_promoted(self):
  rows=self.setup_args()['rows'];rows[-1]['skip_auto_attendance']=1
  self.assertEqual(self.calc(rows=rows)['state'],'Needs Review')
 def test_duplicate_is_review(self):
  rows=self.setup_args()['rows'];rows.append(dict(rows[-1]))
  self.assertEqual(self.calc(rows=rows)['state'],'Needs Review')
 def test_partial_work_requires_review(self):
  rows=self.setup_args()['rows'];rows[-1]['time']='2026-09-21T19:00'
  r=self.calc(rows=rows);self.assertEqual(r['state'],'Needs Review');self.assertEqual(r['snapshot']['verified_hours'],1)
 def test_overrun_preserves_extra_time(self):
  rows=self.setup_args()['rows'];rows[-1]['time']='2026-09-21T21:00'
  r=self.calc(rows=rows);self.assertEqual(r['state'],'Needs Review');self.assertEqual(r['calculation']['unapproved_hours'],1)
 def test_odd_first_last_not_automatically_verified(self):
  args=self.setup_args();args['rows']=args['rows'][:3];args['shift']['working_hours_calculation_based_on']=FIRST_LAST
  self.assertEqual(evaluate_evidence(**args)['state'],'Needs Review')
 def test_alternating_even_sequence_can_interpret_bad_log_type(self):
  rows=self.setup_args()['rows'];rows[-1]['log_type']='IN'
  r=self.calc(rows=rows);self.assertEqual(r['state'],'Verified')
  self.assertTrue(any(i['code']=='direction_reinterpreted' for i in r['issues']))
 def test_strict_does_not_override_bad_direction(self):
  args=self.setup_args();args['rows'][-1]['log_type']='IN';args['shift']['determine_check_in_and_check_out']=STRICT
  self.assertEqual(evaluate_evidence(**args)['state'],'Needs Review')
 def test_authorized_overnight_and_next_entry_remain_separate(self):
  args=self.setup_args();args['authorization'].update(end='2026-09-22T06:00',maximum_hours=12)
  args['rows'][-1].update(time='2026-09-22T06:00',log_type='IN',shift=None,offshift=1)
  args['contexts'].append(context('2026-09-22'))
  args['next_windows']=[{'start':'2026-09-22T07:00','end':'2026-09-22T19:00'}]
  r=evaluate_evidence(**args);self.assertEqual(r['state'],'Verified');self.assertEqual(r['snapshot']['verified_hours'],12)
  args['next_windows'][0]['start']='2026-09-22T05:00'
  self.assertEqual(evaluate_evidence(**args)['state'],'Needs Review')
 def test_holiday_is_not_subtracted_as_ordinary_shift(self):
  r=self.calc(contexts=[context('2026-09-20'),context('2026-09-21',legacy.LEGAL_HOLIDAY)])
  self.assertEqual(r['snapshot']['holiday_100_hours'],2)
 def test_competing_and_incomplete_context_fail_closed(self):
  self.assertEqual(self.calc(competing=True)['state'],'Needs Review')
  self.assertEqual(self.calc(context_complete=False)['state'],'Needs Review')

if __name__=='__main__':unittest.main()
