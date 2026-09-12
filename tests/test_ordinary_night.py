import unittest
from test_overtime_calendar import dt
from powerpro.payroll_rules.ordinary_night import evaluate_night_work
from powerpro.payroll_rules.overtime_shift_evidence import ALTERNATING, EVERY_PAIR, STRICT, FIRST_LAST

class OrdinaryNightTest(unittest.TestCase):
 def run_case(self, stamps, **changes):
  start,end='2026-09-14T18:00:00','2026-09-15T02:00:00'
  shift=dict(name='N',last_sync_of_checkin='2026-09-16',begin_check_in_before_shift_start_time=0,
   allow_check_out_after_shift_end_time=0,determine_check_in_and_check_out=ALTERNATING,working_hours_calculation_based_on=EVERY_PAIR)
  shift.update(changes.pop('shift',{}))
  rows=[dict(name=str(i),time=stamp,log_type=kind,shift='N',shift_start=start,shift_end=end) for i,(stamp,kind) in enumerate(stamps)]
  for i, values in changes.pop('row_changes',{}).items():rows[i].update(values)
  kwargs=dict(rows=rows,shift=shift,context=dict(shift_start=start,shift_end=end,classification='Regular Workday',holiday_list_covers_work_date=True),extensions=[],next_windows=[],now='2026-09-16',basis='Clock overlap')
  kwargs.update(changes)
  return evaluate_night_work(**kwargs)
 def test_no_overtime_document_required(self):
  r=self.run_case([('2026-09-14T18:00','IN'),('2026-09-15T02:00','OUT')])
  self.assertEqual((r['state'],r['night_session']['ordinary_premium_hours'],r['night_session']['overtime_premium_hours']),('Verified',5,0))
 def test_whole_session_rule_excludes_breaks(self):
  r=self.run_case([('2026-09-14T18:00','IN'),('2026-09-14T22:00','OUT'),('2026-09-14T23:00','IN'),('2026-09-15T02:00','OUT')],basis='Whole nocturnal session')
  self.assertEqual(r['night_session']['ordinary_premium_hours'],7)
 def test_extension_premium_is_separate(self):
  r=self.run_case([('2026-09-14T18:00','IN'),('2026-09-15T04:00','IN')],extensions=[{'start':'2026-09-15T02:00','end':'2026-09-15T04:00'}],row_changes={1:{'shift':None}})
  self.assertEqual((r['state'],r['night_session']['ordinary_premium_hours'],r['night_session']['overtime_premium_hours']),('Verified',5,2))
 def test_missing_or_duplicate_punch_requires_review(self):
  for rows in [[('2026-09-14T18:00','IN')],[('2026-09-14T18:00','IN'),('2026-09-14T18:00','OUT')]]:
   self.assertEqual(self.run_case(rows)['state'],'Needs Review')
 def test_sync_waits(self):
  self.assertEqual(self.run_case([('2026-09-14T18:00','IN'),('2026-09-15T02:00','OUT')],shift={'last_sync_of_checkin':None})['state'],'Waiting')
 def test_next_shift_boundary_is_ambiguous(self):
  r=self.run_case([('2026-09-14T18:00','IN'),('2026-09-15T02:00','OUT')],next_windows=[{'start':'2026-09-15T02:00','end':'2026-09-15T10:00'}])
  self.assertEqual(r['state'],'Needs Review')
 def test_all_four_interpretation_modes(self):
  for mode in [ALTERNATING,STRICT]:
   for calc in [EVERY_PAIR,FIRST_LAST]:
    r=self.run_case([('2026-09-14T18:00','IN'),('2026-09-15T02:00','OUT')],shift={'determine_check_in_and_check_out':mode,'working_hours_calculation_based_on':calc})
    self.assertEqual(r['state'],'Verified')
 def test_offshift_is_not_silently_reclassified(self):
  r=self.run_case([('2026-09-14T18:00','IN'),('2026-09-15T02:00','OUT')],row_changes={1:{'shift':None}})
  self.assertEqual(r['state'],'Needs Review')

 def test_certified_session_preserves_original_punches_and_separates_premiums(self):
  r=self.run_case([('2026-09-14T18:00','IN')],shift={'last_sync_of_checkin':None},
   extensions=[{'start':'2026-09-15T02:00','end':'2026-09-15T04:00'}],
   certified_intervals=[{'start':'2026-09-14T18:00','end':'2026-09-14T22:00'},
                        {'start':'2026-09-14T23:00','end':'2026-09-15T03:00'}])
  self.assertEqual((r['state'],r['night_session']['ordinary_premium_hours'],r['night_session']['overtime_premium_hours']),('Verified',4,1))
  self.assertEqual(len(r['source_checkins']),1)
  self.assertEqual(r['source_checkins'][0]['log_type'],'IN')
 def test_certification_does_not_override_calendar_or_finished_window(self):
  interval=[{'start':'2026-09-14T18:00','end':'2026-09-15T02:00'}]
  self.assertEqual(self.run_case([],certified_intervals=interval,now='2026-09-14T20:00')['state'],'Waiting')
  r=self.run_case([],certified_intervals=interval,context=dict(shift_start='2026-09-14T18:00',shift_end='2026-09-15T02:00',classification='Regular Workday',holiday_list_covers_work_date=False))
  self.assertEqual(r['state'],'Needs Review')
 def test_certified_overlap_and_unapproved_time_are_rejected(self):
  interval={'start':'2026-09-14T18:00','end':'2026-09-15T02:00'}
  with self.assertRaises(ValueError):self.run_case([],certified_intervals=[interval,interval])
  r=self.run_case([],certified_intervals=[dict(start='2026-09-14T18:00',end='2026-09-15T03:00')])
  self.assertEqual(r['state'],'Needs Review')

 def test_expanded_window_preserves_physical_overrun_and_original_classification(self):
  r=self.run_case([('2026-09-14T18:00','IN'),('2026-09-15T06:00','IN')],
   row_changes={1:{'shift':None}},observation_window={'start':'2026-09-14T18:00','end':'2026-09-15T06:00'})
  self.assertEqual(r['state'],'Needs Review')
  self.assertEqual(r['night_session']['ordinary_premium_hours'],5)
  self.assertEqual(r['unapproved_intervals'],[{'start':'2026-09-15T02:00:00','end':'2026-09-15T06:00:00'}])
  self.assertEqual(r['source_checkins'][-1]['log_type'],'IN')
  self.assertEqual(r['interpretations'][-1]['reason'],'historical_observation')
 def test_expanded_window_waits_for_actual_end_and_sync(self):
  window={'start':'2026-09-14T18:00','end':'2026-09-15T06:00'}
  for kwargs in [dict(now='2026-09-15T05:00'),dict(shift={'last_sync_of_checkin':'2026-09-15T05:00'})]:
   r=self.run_case([('2026-09-14T18:00','IN'),('2026-09-15T06:00','OUT')],observation_window=window,**kwargs)
   self.assertEqual(r['state'],'Waiting')
 def test_prior_shift_is_not_reinterpreted_as_current_session(self):
  r=self.run_case([('2026-09-14T04:00','IN'),('2026-09-15T02:00','OUT')],
   row_changes={0:{'shift':'Other'}},observation_window={'start':'2026-09-14T03:00','end':'2026-09-15T02:00'},
   next_windows=[{'shift':'Other','start':'2026-09-13T22:00','end':'2026-09-14T06:00','relation':'previous'}])
  self.assertEqual(r['state'],'Needs Review')
  self.assertTrue(any(i['code']=='adjacent_shift_overlap' for i in r['issues']))
 def test_next_shift_conflict_still_blocks_expanded_window(self):
  r=self.run_case([('2026-09-14T18:00','IN'),('2026-09-15T06:00','OUT')],
   observation_window={'start':'2026-09-14T18:00','end':'2026-09-15T06:00'},
   next_windows=[{'start':'2026-09-15T05:00','end':'2026-09-15T13:00'}])
  self.assertTrue(any(i['code']=='next_shift_overlap' for i in r['issues']))

if __name__=='__main__':unittest.main()
