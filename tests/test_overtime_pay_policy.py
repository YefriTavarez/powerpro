import copy
import unittest
from test_overtime_calendar import dt
from powerpro.payroll_rules.overtime_pay_policy import validate_policy,classify_night_session,rates,review_summary


def policy():
    return dict(company='DEV',valid_from='2026-09-01',valid_until='2026-09-30',approval_reference='Approved examples',
                weekly_threshold=68,regular_percent=35,extraordinary_percent=100,night_percent=15,
                weekly_rest_percent=100,night_basis='Clock overlap',premium_combination='Additive on base hour')


class PolicyTest(unittest.TestCase):
    def test_review_summary_preserves_evaluated_revision_and_filters_private_inputs(self):
        p=dict(policy(),name='PINNED-OLD',night_percent=15)
        result={'input':{'pay_policy':p,'configuration':{'night_hours_rate':20},
                        'rate_basis':{'base':987654,'name':'PRIVATE-SALARY'}},
                'snapshot':{'night_hours':0,'regular_35_hours':2},
                'calculation':{'weekly_evidence_complete':True,'holiday_base_covered_hours':0}}
        before=copy.deepcopy(result)
        summary=review_summary(result)
        self.assertEqual(summary['policy']['name'],'PINNED-OLD')
        self.assertEqual(summary['policy']['night_percent'],15)
        self.assertEqual(summary['hours']['night_hours'],0)
        self.assertTrue(summary['weekly_evidence_complete'])
        self.assertNotIn('PRIVATE-SALARY',str(summary))
        self.assertNotIn('rate_basis',summary)
        self.assertEqual(result,before)

    def test_review_summary_separates_clock_night_from_whole_session_premium(self):
        worked=[{'start':'2026-09-21T18:00:00','end':'2026-09-22T00:00:00'}]
        overtime=[{'start':'2026-09-21T20:00:00','end':'2026-09-22T00:00:00'}]
        for basis,ot,ordinary in [('Clock overlap',3,0),('Whole nocturnal session',4,2)]:
            night=classify_night_session(worked,overtime,basis=basis)
            summary=review_summary({'input':{'pay_policy':dict(policy(),night_basis=basis)},
                'night_session':night,'snapshot':{'night_hours':night['overtime_premium_hours']}})
            self.assertEqual(summary['night']['clock_night_hours'],3)
            self.assertEqual(summary['hours']['night_hours'],ot)
            self.assertEqual(summary['night']['ordinary_premium_hours'],ordinary)

    def test_review_summary_does_not_invent_policy_or_missing_hours(self):
        summary=review_summary({'input':{'configuration':{'night_hours_rate':15}}})
        self.assertIsNone(summary['policy'])
        self.assertIsNone(summary['hours']['night_hours'])
        self.assertIsNone(summary['weekly_evidence_complete'])

    def test_requires_explicit_reference_and_supported_rules(self):
        validate_policy(policy())
        for field in ['approval_reference','night_basis','premium_combination','company','valid_from']:
            p=policy();p[field]=''
            with self.assertRaises(ValueError):validate_policy(p)
    def test_floor_rates_and_nonfinite_values(self):
        for field,minimum in [('regular_percent',35),('extraordinary_percent',100),('night_percent',15),('weekly_rest_percent',100)]:
            for value in [minimum-.01,float('nan'),float('inf')]:
                p=policy();p[field]=value
                with self.assertRaises(ValueError):validate_policy(p)
    def test_effective_dates_and_weekly_threshold(self):
        p=policy();p['valid_until']='2026-08-01'
        with self.assertRaises(ValueError):validate_policy(p)
        for value in [0,69,float('nan')]:
            p=policy();p['weekly_threshold']=value
            with self.assertRaises(ValueError):validate_policy(p)
    def test_compensatory_equivalence_must_be_explicit(self):
        p=policy();p['enable_compensatory']=1
        with self.assertRaises(ValueError):validate_policy(p)
        p.update(leave_type='Compensatory',hours_per_leave_day=8,leave_increment=.5,rest_hours_per_worked_hour=1)
        validate_policy(p)
        p['hours_per_leave_day']=0
        with self.assertRaises(ValueError):validate_policy(p)
    def test_rates_use_approved_policy_without_mutation(self):
        p=policy();p['regular_percent']=40;before=copy.deepcopy(p)
        self.assertEqual(rates(p)['regular_overtime_percent'],40);self.assertEqual(p,before)
    def night(self,end,basis='Whole nocturnal session'):
        worked=[{'start':'2026-09-21T18:00','end':end}]
        ot=[{'start':'2026-09-21T20:00','end':end}]
        return classify_night_session(worked,ot,basis=basis)
    def test_three_hour_boundary_without_rounded_promotion(self):
        for end,kind in [('2026-09-21T23:59','Mixta'),('2026-09-22T00:00','Nocturna'),('2026-09-22T00:01','Nocturna')]:
            r=self.night(end);self.assertEqual(r['classification'],kind)
        self.assertEqual(self.night('2026-09-21T23:59:59')['classification'],'Mixta')
    def test_whole_session_differs_from_clock_overlap_explicitly(self):
        full=self.night('2026-09-22T00:00');clock=self.night('2026-09-22T00:00','Clock overlap')
        self.assertEqual((full['premium_hours'],full['overtime_premium_hours'],full['ordinary_premium_hours']),(6,4,2))
        self.assertEqual((clock['premium_hours'],clock['overtime_premium_hours']),(3,3))
    def test_breaks_are_excluded_from_session_threshold(self):
        r=classify_night_session([{'start':'2026-09-21T18:00','end':'2026-09-21T22:00'},
                                 {'start':'2026-09-21T23:00','end':'2026-09-22T00:00'}],[],basis='Whole nocturnal session')
        self.assertEqual((r['classification'],r['clock_night_hours']),('Mixta',2))
    def test_ordinary_night_work_does_not_require_fake_overtime(self):
        r=classify_night_session([{'start':'2026-09-21T22:00','end':'2026-09-22T06:00'}],[],basis='Whole nocturnal session')
        self.assertEqual((r['ordinary_premium_hours'],r['overtime_premium_hours']),(8,0))
    def test_clock_boundaries_preserve_seconds(self):
        for a,b in [('2026-09-21T20:59:59','2026-09-21T21:00:01'),('2026-09-22T06:59:59','2026-09-22T07:00:01')]:
            r=classify_night_session([{'start':a,'end':b}],[],basis='Clock overlap')
            self.assertEqual(r['clock_night_hours'],.0003)
    def test_invalid_or_uncontained_intervals_are_rejected(self):
        valid={'start':'2026-09-21T22:00','end':'2026-09-22T00:00'}
        for worked,extra in [([valid,valid],[]),([valid],[{'start':'2026-09-22T01:00','end':'2026-09-22T02:00'}]),
                             ([{'start':valid['end'],'end':valid['start']}],[])]:
            with self.assertRaises(ValueError):classify_night_session(worked,extra,basis='Clock overlap')


if __name__=='__main__':unittest.main()
