import unittest
from test_overtime_calendar import dt
from powerpro.payroll_rules.overtime_manual_session import evaluate_manual_session

class ManualSessionTest(unittest.TestCase):
 def result(self,**override):
  declaration={'full_session':True,'reference':'Registro del supervisor',
   'intervals':[{'start':'2026-09-14T08:00','end':'2026-09-14T12:00'},{'start':'2026-09-14T13:00','end':'2026-09-14T19:00'}]}
  declaration.update(override)
  return evaluate_manual_session(declaration=declaration,authorization={'start':'2026-09-14T18:00','end':'2026-09-14T20:00','maximum_hours':2,'shift':'D'},
   rows=[],contexts=[{'date':'2026-09-14','shift_start':'2026-09-14T08:00','shift_end':'2026-09-14T18:00','classification':'Regular Workday','holiday_list_covers_work_date':True}],now=dt('2026-09-15T00:00'))
 def test_complete_session_without_manufactured_punches(self):
  r=self.result();self.assertEqual(r['source_checkins'],[]);self.assertEqual(r['snapshot']['verified_hours'],1)
  self.assertEqual(len(r['worked_intervals']),2);self.assertEqual(r['certified_sessions'][0]['shift'],'D')
 def test_requires_explicit_attestation_and_reference(self):
  for change in [{'full_session':False},{'full_session':'true'},{'reference':''}]:
   with self.assertRaises(ValueError):self.result(**change)
 def test_certified_day_needs_no_synthetic_checkin_or_assumed_hours(self):
  from powerpro.payroll_rules.overtime_actual_week import collect_weekly_work
  r=self.result()
  kwargs=dict(start='2026-09-14T00:00:00',cutoff='2026-09-14T20:00:00',rows=[],policies={'D':{}},attendances=[],
   schedules=[{'date':'2026-09-14','shift':'D','shift_start':'2026-09-14T08:00','shift_end':'2026-09-14T18:00',
               'classification':'Regular Workday','holiday_list_covers_work_date':True}],accepted_intervals=r['worked_intervals'])
  self.assertFalse(collect_weekly_work(**kwargs)['complete'])
  week=collect_weekly_work(**kwargs,certified_sessions=r['certified_sessions'])
  self.assertTrue(week['complete']);self.assertEqual(week['coverage'][0]['state'],'hr_certified_session')
  hours=sum((dt(x['end'])-dt(x['start'])).total_seconds()/3600 for x in week['intervals'])
  self.assertEqual(hours,10)
 def test_rejects_overlap_and_outside_session(self):
  for rows in [[{'start':'2026-09-14T07:00','end':'2026-09-14T19:00'}],
               [{'start':'2026-09-14T08:00','end':'2026-09-14T19:00'},{'start':'2026-09-14T18:00','end':'2026-09-14T20:00'}]]:
   with self.assertRaises(ValueError):self.result(intervals=rows)

if __name__=='__main__':unittest.main()
