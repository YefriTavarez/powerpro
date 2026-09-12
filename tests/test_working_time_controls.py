import unittest
from test_overtime_calendar import dt
from powerpro.payroll_rules.working_time_controls import evaluate


def row(a,b):return {'start':a,'end':b}
def run(work,**kw):
    return evaluate(worked_intervals=work,weekly_intervals=kw.pop('weekly_intervals',work),session_complete=True,weekly_complete=True,
        week_start='2026-09-07 00:00:00',cutoff=kw.pop('cutoff','2026-09-09 00:00:00'),**kw)
def control(result,code):return next(r for r in result['controls'] if r['code']==code)


class ControlsTest(unittest.TestCase):
 def test_exact_daily_boundary_and_seconds(self):
  work=[row('2026-09-07 08:00:00','2026-09-07 12:00:00'),row('2026-09-07 13:00:00','2026-09-07 17:00:00')]
  self.assertEqual(control(run(work),'daily_work')['status'],'Within evaluated limit')
  work[-1]['end']='2026-09-07 17:00:01'
  self.assertEqual(control(run(work),'daily_work')['status'],'Review')
 def test_short_pause_does_not_reset_continuous_counter(self):
  work=[row('2026-09-07 08:00:00','2026-09-07 12:00:00'),row('2026-09-07 12:59:59','2026-09-07 13:00:00')]
  self.assertEqual(control(run(work),'work_break')['status'],'Review')
  work[1]=row('2026-09-07 13:00:00','2026-09-07 17:00:00')
  self.assertEqual(control(run(work),'work_break')['status'],'Within evaluated limit')
 def test_five_hour_option_requires_ninety_minutes(self):
  work=[row('2026-09-07 08:00:00','2026-09-07 13:00:00'),row('2026-09-07 14:00:00','2026-09-07 17:00:00')]
  self.assertEqual(control(run(work,break_rule='Ninety minutes after five'),'work_break')['status'],'Review')
  work[1]['start']='2026-09-07 14:30:00'
  self.assertEqual(control(run(work,break_rule='Ninety minutes after five'),'work_break')['status'],'Within evaluated limit')
 def test_profile_requires_documented_basis(self):
  with self.assertRaises(ValueError):run([],profile='Continuous operation')
  r=run([],profile='Continuous operation',reference='Documented industrial process')
  self.assertEqual(control(r,'work_break')['status'],'Documented regime required')
  self.assertFalse(r['compliance_certified']);self.assertFalse(r['affects_payment'])
 def test_first_last_does_not_certify_breaks(self):
  self.assertEqual(control(run([],breaks_observable=False),'work_break')['status'],'Incomplete')
 def test_incomplete_week_still_proves_lower_bound_exceeded(self):
  data=dict(worked_intervals=[],weekly_intervals=[row('2026-09-07 00:00:00','2026-09-09 00:00:00')],
   session_complete=False,weekly_complete=False,week_start='2026-09-07',cutoff='2026-09-10')
  self.assertEqual(control(evaluate(**data),'weekly_work')['status'],'Review')
  data['weekly_intervals']=[]
  self.assertEqual(control(evaluate(**data),'weekly_work')['status'],'Incomplete')
 def test_sunday_to_monday_not_one_week(self):
  r=run([row('2026-09-13 22:00:00','2026-09-14 02:00:00')],cutoff='2026-09-14 02:00:00')
  self.assertEqual([x['observed'] for x in r['controls'] if x['code']=='weekly_work'],[2,2])
 def test_quarter_union_clipping_and_cause(self):
  q=[row('2026-06-30 22:00:00','2026-07-01 02:00:00')]*2
  r=run([],quarter_intervals=q,quarter_start='2026-07-01',quarter_end='2026-10-01')
  self.assertEqual(control(r,'quarterly_extension')['observed'],2)
  self.assertEqual(control(r,'quarterly_extension')['status'],'Applicability review')
  r=run([],quarter_intervals=q,quarter_start='2026-07-01',quarter_end='2026-10-01',quarterly_basis='Extraordinary workload')
  self.assertEqual(control(r,'quarterly_extension')['status'],'Incomplete')
 def test_quarter_threshold_raw_seconds(self):
  kw=dict(quarter_start='2026-07-01',quarter_end='2026-10-01',quarterly_basis='Extraordinary workload')
  q=[row('2026-07-01 00:00:00','2026-07-04 08:00:00')]
  self.assertEqual(control(run([],quarter_intervals=q,**kw),'quarterly_extension')['status'],'Incomplete')
  q[0]['end']='2026-07-04 08:00:01'
  self.assertEqual(control(run([],quarter_intervals=q,**kw),'quarterly_extension')['status'],'Review')
 def test_short_rest_does_not_pass_at_rounded_boundary(self):
  r=run([],rest_start='2026-09-07 00:00:00',rest_end='2026-09-08 11:59:59')
  self.assertEqual(control(r,'weekly_continuous_rest')['status'],'Review')
 def test_rest_duration_and_evidence_not_presumption(self):
  r=run([],rest_start='2026-09-07 00:00:00',rest_end='2026-09-08 12:00:00')
  self.assertEqual(control(r,'weekly_continuous_rest')['status'],'Enjoyment unverified')
  r=run([row('2026-09-07 08:00:00','2026-09-07 09:00:00')],rest_start='2026-09-07 00:00:00',rest_end='2026-09-08 12:00:00')
  self.assertEqual(control(r,'weekly_continuous_rest')['recorded_work_hours'],1)
  self.assertEqual(control(r,'weekly_continuous_rest')['status'],'Review')
 def test_overlapping_work_counted_once(self):
  r=run([row('2026-09-07 08:00:00','2026-09-07 12:00:00')]*2)
  self.assertEqual(control(r,'daily_work')['observed'],4)

if __name__=='__main__':unittest.main()
