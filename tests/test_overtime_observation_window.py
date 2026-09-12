import unittest
from copy import deepcopy
from test_overtime_calendar import dt,context
import test_overtime_evidence as evidence_fixture
from powerpro.payroll_rules.overtime_observation_window import normalize_window
from powerpro.payroll_rules.overtime_evidence import evaluate_evidence
from powerpro.payroll_rules.overtime_manual_session import evaluate_manual_session

class ObservationWindowTest(unittest.TestCase):
 def args(self):
  args=evidence_fixture.EvidenceTest().setup_args()
  args['shift']['allow_check_out_after_shift_end_time']=0
  args['rows'][-1].update(time='2026-09-22T06:00',shift=None,offshift=1)
  args['contexts'].append(context('2026-09-22'))
  args['observation_window']={'start':'2026-09-21T08:00','end':'2026-09-22T06:00'}
  return args
 def test_original_authorization_remains_capped_but_physical_overrun_is_visible(self):
  args=self.args();original=deepcopy(args['authorization']);r=evaluate_evidence(**args)
  self.assertEqual(args['authorization'],original);self.assertEqual(r['snapshot']['verified_hours'],2)
  self.assertEqual(r['calculation']['unapproved_hours'],10)
  self.assertEqual(r['worked_intervals'][-1]['end'],'2026-09-22T06:00:00')
  self.assertTrue(any(i.get('group')=='historical_observation' for i in r['interpretations']))
  self.assertEqual(r['state'],'Needs Review')
 def test_default_does_not_infer_a_window(self):
  args=self.args();args.pop('observation_window');self.assertEqual(evaluate_evidence(**args)['state'],'Needs Review')
 def test_actual_expanded_end_controls_sync(self):
  args=self.args();args['shift']['last_sync_of_checkin']='2026-09-22T05:59'
  self.assertEqual(evaluate_evidence(**args)['state'],'Waiting')
 def test_next_shift_overlap_still_requires_review(self):
  args=self.args();args['next_windows']=[{'start':'2026-09-22T05:00','end':'2026-09-22T18:00'}]
  self.assertTrue(any(i['code']=='next_shift_overlap' for i in evaluate_evidence(**args)['issues']))
 def test_explicit_manual_session_can_preserve_overrun_without_fake_punches(self):
  args=self.args();declaration={'full_session':True,'reference':'Signed full session','intervals':[
   {'start':'2026-09-21T08:00','end':'2026-09-21T12:00'}, {'start':'2026-09-21T13:00','end':'2026-09-22T06:00'}]}
  r=evaluate_manual_session(declaration=declaration,rows=[],**{k:args[k] for k in ['authorization','contexts','now','observation_window']})
  self.assertEqual(r['source_checkins'],[]);self.assertEqual(r['snapshot']['verified_hours'],2)
  self.assertEqual(r['calculation']['unapproved_hours'],10)
 def test_rejects_truncation_overlong_reversed_or_timezone_window(self):
  for value in [{'start':'2026-09-21T09:00','end':'2026-09-21T20:00'},
   {'start':'2026-09-21T08:00','end':'2026-09-21T19:00'},
   {'start':'2026-09-21T08:00','end':'2026-09-22T08:01'},
   {'start':'2026-09-21T08:00Z','end':'2026-09-21T20:00Z'},{}]:
   with self.assertRaises(ValueError):normalize_window(value,'2026-09-21T08:00','2026-09-21T20:00')

if __name__=='__main__':unittest.main()
