"""Authorization-aware overnight proposals, no Frappe site or database writes."""
import copy
import unittest
from unittest.mock import patch
from test_overtime_calendar import Record,frappe,dt
from powerpro.payroll_rules.overtime_overnight import compare_overnight
from powerpro.payroll_rules.overtime_shift_evidence import ALTERNATING,STRICT,EVERY_PAIR,FIRST_LAST
from powerpro.controllers.overtime_overnight import get_overnight_comparison


def punches():
    return [dict(name='IN',time='2026-09-21T08:00',log_type='IN',shift='DAY',shift_start='2026-09-21T08:00',shift_end='2026-09-21T18:00'),
            dict(name='MORNING',time='2026-09-22T06:00',log_type='IN',offshift=1)]


def policies():
    return {'DAY':dict(name='DAY',start_time='08:00',end_time='18:00',begin_check_in_before_shift_start_time=60,
        allow_check_out_after_shift_end_time=60,determine_check_in_and_check_out=ALTERNATING,
        working_hours_calculation_based_on=EVERY_PAIR,last_sync_of_checkin='2026-09-22T07:00')}


class OvernightTest(unittest.TestCase):
    def calc(self,**kw):
        args=dict(authorization={'start':'2026-09-21T18:00','end':'2026-09-22T06:00','shift':'DAY'},
                  checkins=punches(),policies=policies(),next_windows=[{'shift':'DAY','start':'2026-09-22T07:00','end':'2026-09-22T19:00'}],
                  now='2026-09-22T08:00',context_complete=True)
        args.update(kw);return compare_overnight(**args)
    def test_in_at_six_can_belong_to_previous_authorized_session(self):
        x=self.calc()
        self.assertEqual(x['interpretations'][0]['interpretation'],'Previous authorized session')
        self.assertEqual(x['intervals'][-1]['end'],'2026-09-22T06:00:00')
        self.assertFalse(x['settlement_eligible'])
        self.assertIn('punch_sequence_requires_review',x['coverage_blockers'])
    def test_explicit_out_can_be_provisional_when_coverage_signals_pass(self):
        rows=punches();rows[-1]['log_type']='OUT'
        x=self.calc(checkins=rows)
        self.assertEqual(x['status'],'Provisional');self.assertFalse(x['settlement_eligible'])
    def test_no_punches_are_changed(self):
        rows=punches();before=copy.deepcopy(rows)
        self.calc(checkins=rows)
        self.assertEqual(rows,before)
    def test_next_shift_overlap_requires_review(self):
        x=self.calc(next_windows=[{'shift':'EARLY','start':'2026-09-22T05:00','end':'2026-09-22T15:00'}])
        self.assertEqual(x['interpretations'][0]['interpretation'],'Needs Review')
        self.assertIn('next_shift_overlap',x['coverage_blockers']);self.assertEqual(x['intervals'],[])
    def test_later_new_entry_stays_outside_previous_authorization(self):
        rows=punches()+[dict(name='NEW',time='2026-09-22T08:00',log_type='IN')]
        x=self.calc(checkins=rows)
        self.assertNotIn('NEW',[r['checkin'] for r in x['interpretations']])
        self.assertEqual(x['intervals'][-1]['end'],'2026-09-22T06:00:00')
    def test_competing_authorizations_do_not_choose_a_group(self):
        x=self.calc(competing=True)
        self.assertEqual(x['intervals'],[])
        self.assertIn('overlapping_authorizations',x['coverage_blockers'])
        self.assertTrue(all(r['interpretation']=='Needs Review' for r in x['interpretations']))
    def test_missing_or_permission_filtered_context_does_not_group(self):
        x=self.calc(context_complete=False)
        self.assertEqual(x['intervals'],[])
    def test_excluded_marks_remain_excluded(self):
        rows=punches()
        for r in rows:r['skip_auto_attendance']=1
        x=self.calc(checkins=rows)
        self.assertEqual(x['intervals'],[])
        self.assertIn('excluded_checkins',x['coverage_blockers'])
    def test_never_invents_anchor_from_authorization(self):
        x=self.calc(checkins=punches()[1:])
        self.assertIn('missing_captured_anchor',x['coverage_blockers'])
        self.assertEqual(x['intervals'],[])
    def test_missing_exit_does_not_create_one_at_authorized_end(self):
        x=self.calc(checkins=punches()[:1])
        self.assertEqual(x['intervals'],[])
        self.assertIn('missing_worked_interval',x['coverage_blockers'])
    def test_sync_and_future_window_are_explicit_blockers(self):
        p=policies();p['DAY']['last_sync_of_checkin']=None
        x=self.calc(policies=p,now='2026-09-22T05:00')
        self.assertIn('sync_not_confirmed',x['coverage_blockers'])
        self.assertIn('authorization_not_ended',x['coverage_blockers'])
    def test_strict_mode_does_not_silently_relabel_in_as_out(self):
        p=policies();p['DAY']['determine_check_in_and_check_out']=STRICT
        x=self.calc(policies=p)
        self.assertEqual(x['intervals'],[])
    def test_breaks_survive_extended_group(self):
        rows=punches()
        for clock,kind in [('12:00','OUT'),('13:00','IN')]:
            r=copy.deepcopy(rows[0]);r.update(name=clock,time='2026-09-21T'+clock,log_type=kind);rows.append(r)
        x=self.calc(checkins=rows)
        self.assertEqual(len(x['intervals']),2)
        self.assertEqual(x['intervals'][0]['end'],'2026-09-21T12:00:00')
    def test_daytime_not_applicable(self):
        x=self.calc(authorization={'start':'2026-09-21T18:00','end':'2026-09-21T22:00','shift':'DAY'})
        self.assertFalse(x['applicable'])
    def test_long_session_requires_review(self):
        x=self.calc(authorization={'start':'2026-09-21T18:00','end':'2026-09-22T10:00','shift':'DAY'})
        self.assertIn('extended_session_over_24h',x['coverage_blockers'])
    def test_invalid_window_rejected(self):
        with self.assertRaises(ValueError):self.calc(authorization={'start':'2026-09-21T18:00','end':'2026-09-21T17:00','shift':'DAY'})


class AdapterTest(unittest.TestCase):
    def setUp(self):
        self.doc=Record(doctype='Overtime Authorization',docstatus=1,name='AUTH',employee='EMP',shift_type='DAY',authorization_start='2026-09-21T18:00',authorization_end='2026-09-22T06:00')
        self.rows=punches();self.policy=policies()['DAY'];self.assignments=[]
    def query(self,doctype,**kw):
        return {'Employee':[Record(name='EMP',default_shift='DAY')],'Employee Checkin':self.rows,'Shift Assignment':self.assignments,'Shift Type':[self.policy]}[doctype]
    def all_query(self,doctype,**kw):
        if doctype=='Employee Checkin':return [r['name'] for r in self.rows]
        if doctype=='Shift Assignment':return [r['name'] for r in self.assignments]
        return []
    def calc(self,all_query=None):
        with patch.object(frappe,'has_permission',return_value=True),patch.object(frappe,'get_list',side_effect=self.query),patch.object(frappe,'get_all',side_effect=all_query or self.all_query):
            return get_overnight_comparison(self.doc)
    def test_uses_default_shift_and_records_digest(self):
        x=self.calc();self.assertTrue(x['available']);self.assertTrue(x['source_hash']);self.assertTrue(x['intervals'])
    def test_assignment_overrides_default_for_next_day(self):
        self.assignments=[{'name':'ASSIGN','shift_type':'DAY','start_date':'2026-09-22','end_date':'2026-09-22'}]
        self.policy['begin_check_in_before_shift_start_time']=180
        x=self.calc();self.assertIn('next_shift_overlap',x['coverage_blockers'])
    def test_hidden_assignment_suppresses_proposal_without_exposing_id(self):
        def query(doctype,**kw):return ['HIDDEN'] if doctype=='Shift Assignment' else self.all_query(doctype,**kw)
        x=self.calc(query);self.assertEqual(x['intervals'],[]);self.assertNotIn('HIDDEN',str(x))
    def test_hidden_punch_suppresses_proposal_without_exposing_id(self):
        def query(doctype,**kw):return self.all_query(doctype,**kw)+(['HIDDEN'] if doctype=='Employee Checkin' else [])
        x=self.calc(query);self.assertEqual(x['intervals'],[]);self.assertNotIn('HIDDEN',str(x))
    def test_denied_context_stops_reads(self):
        with patch.object(frappe,'has_permission',return_value=False),patch.object(frappe,'get_list') as query:
            self.assertFalse(get_overnight_comparison(self.doc)['available']);query.assert_not_called()
    def test_draft_and_retroactive_are_not_used_as_prior_authorization(self):
        for field,value in [('docstatus',0),('doctype','Retroactive Overtime Adjustment')]:
            old=self.doc[field];self.doc[field]=value
            self.assertFalse(get_overnight_comparison(self.doc)['available']);self.doc[field]=old
    def test_truncation_has_no_partial_interpretation(self):
        self.rows=[{}]*2001
        self.assertFalse(self.calc()['available'])


if __name__=='__main__':unittest.main()
