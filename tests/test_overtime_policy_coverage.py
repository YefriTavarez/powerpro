import copy
import unittest
from powerpro.payroll_rules.overtime_policy_coverage import (
    compose_coverage, policy_value, policy_names, RULE_FIELDS, VERSIONS,
)
from powerpro.payroll_rules.overtime_pay_policy import classify_night_session, review_summary


def policy(name='FIRST', start='2026-08-14', end='2026-08-16'):
    return dict(name=name, company='TEST', valid_from=start, valid_until=end,
        approval_reference='Synthetic approved rule example', approved_by='Reviewer', approved_on='2026-08-01',
        weekly_threshold=68, regular_percent=35, extraordinary_percent=100, night_percent=15,
        night_basis='Clock overlap', premium_combination='Additive on base hour', weekly_rest_cash=1,
        weekly_rest_percent=100, enable_compensatory=0, leave_type=None, hours_per_leave_day=8,
        leave_increment=.5, rest_hours_per_worked_hour=1, weekly_rest_duration_hours=36,
        weekly_rest_credit_hours=8, holiday_weekly_rest_mode='Single highest premium',
        holiday_weekly_rest_compensatory=0)


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.first=policy()
        self.second=policy('SECOND','2026-08-17','2026-08-20')

    def compose(self, rows=None, **kw):
        return compose_coverage(rows or [self.first,self.second], kw.get('company','TEST'),
                                kw.get('start','2026-08-16'),kw.get('last','2026-08-17'))

    def test_contiguous_rules_keep_original_versions_and_input_unchanged(self):
        before=copy.deepcopy([self.first,self.second])
        merged=self.compose([self.second,self.first])
        self.assertEqual(policy_names(merged),['FIRST','SECOND'])
        self.assertEqual(merged['name'],'FIRST')
        self.assertEqual(merged['valid_until'],'2026-08-20')
        self.assertEqual(merged[VERSIONS][0]['valid_until'],'2026-08-16')
        self.assertEqual([self.first,self.second],before)
        self.assertEqual(merged[VERSIONS][1]['approved_by'],'Reviewer')

    def test_single_policy_representation_is_unchanged(self):
        self.assertEqual(self.compose([self.first],last='2026-08-16'),policy_value(self.first))
        self.assertNotIn(VERSIONS,policy_value(self.first))

    def test_equivalent_optional_zero_and_text_defaults(self):
        self.second['enable_compensatory']=None
        self.second['leave_type']=''
        self.assertEqual(policy_names(self.compose()),['FIRST','SECOND'])

    def test_different_approval_metadata_is_not_a_rate_change(self):
        self.second.update(approved_by='Other',approval_reference='Another approval')
        self.compose()

    def test_every_rule_change_is_rejected(self):
        for key in RULE_FIELDS:
            with self.subTest(key=key):
                changed=copy.deepcopy(self.second)
                value=changed.get(key)
                changed[key]=str(value)+' different' if isinstance(value,str) or key=='leave_type' else (value or 0)+1
                with self.assertRaises(ValueError):self.compose([self.first,changed])

    def test_gap_overlap_duplicate_partial_and_wrong_company(self):
        for changes in [dict(valid_from='2026-08-18'),dict(valid_from='2026-08-16'),
                        dict(company='OTHER'),dict(valid_until='2026-08-16')]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.compose([self.first,{**self.second,**changes}])
        with self.assertRaises(ValueError):self.compose([self.first,self.first])
        with self.assertRaises(ValueError):self.compose([self.first])
        with self.assertRaises(ValueError):self.compose(start='2026-08-13')
        with self.assertRaises(ValueError):self.compose(last='2026-08-21')
        with self.assertRaises(ValueError):self.compose(company='OTHER')
        with self.assertRaises(ValueError):compose_coverage([], 'TEST','2026-08-16','2026-08-17')

    def test_three_periods_are_supported_only_when_contiguous(self):
        third=policy('THIRD','2026-08-21','2026-08-22')
        self.assertEqual(policy_names(self.compose([third,self.second,self.first],last='2026-08-22')),
                         ['FIRST','SECOND','THIRD'])

    def test_review_summary_lists_versions_without_private_approval_notes(self):
        p=self.compose()
        summary=review_summary({'input':{'pay_policy':p}})
        self.assertEqual(summary['policy'][VERSIONS], [
            dict(name='FIRST',valid_from='2026-08-14',valid_until='2026-08-16'),
            dict(name='SECOND',valid_from='2026-08-17',valid_until='2026-08-20')])
        self.assertNotIn('approval_reference',str(summary))

    def test_overnight_break_leaves_eleven_worked_and_eight_night_hours(self):
        p=self.compose()
        intervals=[dict(start='2026-08-16 18:00',end='2026-08-16 21:00'),
                   dict(start='2026-08-16 22:00',end='2026-08-17 06:00')]
        result=classify_night_session(intervals,intervals,basis=p['night_basis'])
        self.assertEqual((result['worked_hours'],result['overtime_premium_hours']),(11,8))

if __name__=='__main__':unittest.main()
