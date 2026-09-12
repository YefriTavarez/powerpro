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

if __name__=='__main__':unittest.main()
