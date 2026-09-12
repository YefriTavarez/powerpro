import unittest
from test_overtime_calendar import dt
from powerpro.payroll_rules.overtime_rest import rest_entitlement,validate_rest_schedule
from powerpro.payroll_rules.overtime_cash_settlement import calculate_cash_settlement


def policy():return {'enable_compensatory':1,'hours_per_leave_day':8,'rest_hours_per_worked_hour':1,
                     'weekly_rest_duration_hours':36,'weekly_rest_credit_hours':8}


class RestTest(unittest.TestCase):
    def test_ordinary_entitlement_separates_credit_days_and_continuous_hours(self):
        r=rest_entitlement(policy(),4)
        self.assertEqual((r['credit_hours'],r['minimum_rest_hours'],r['required_leave_days']),(4,4,.5))
    def test_weekly_rest_is_not_proportional_to_hours_worked(self):
        r=rest_entitlement(policy(),2,weekly_rest=True)
        self.assertEqual((r['credit_hours'],r['minimum_rest_hours'],r['required_leave_days']),(8,36,1))
    def test_no_implicit_conversion_or_disabled_rest(self):
        for change in [{'enable_compensatory':0},{'weekly_rest_credit_hours':0},{'weekly_rest_duration_hours':35}]:
            p=policy();p.update(change)
            with self.assertRaises(ValueError):rest_entitlement(p,2,weekly_rest=True)
    def test_invalid_and_nonfinite_hours(self):
        for hours in [0,-1,float('nan'),float('inf')]:
            with self.assertRaises(ValueError):rest_entitlement(policy(),hours)
    def schedule(self,start,end,weekly=True):
        return validate_rest_schedule(start,end,work_date='2026-09-13',authorization_end='2026-09-13T20:00',
                                      entitlement=rest_entitlement(policy(),4,weekly_rest=weekly))
    def test_following_week_accepts_full_rest(self):
        r=self.schedule('2026-09-15T18:00','2026-09-17T06:00')
        self.assertEqual(r['hours'],36)
    def test_too_short_or_wrong_week_rejected(self):
        for a,b in [('2026-09-15T18:00','2026-09-17T05:59:59'),('2026-09-13T21:00','2026-09-15T09:00'),('2026-09-20T18:00','2026-09-22T06:00')]:
            with self.assertRaises(ValueError):self.schedule(a,b)
    def test_ordinary_rest_after_work_with_exact_duration(self):
        self.assertEqual(self.schedule('2026-09-15T13:00','2026-09-15T17:00',False)['hours'],4)
        with self.assertRaises(ValueError):self.schedule('2026-09-13T17:00','2026-09-13T21:00',False)
    def test_weekly_cash_requires_explicit_optin_and_pays_base_once(self):
        self.assertEqual(calculate_cash_settlement(hourly_rate=100,weekly_rest_hours=2)['unsettled_weekly_rest_hours'],2)
        r=calculate_cash_settlement(hourly_rate=100,weekly_rest_hours=2,weekly_rest_overtime_percent=100,night_hours=1)
        self.assertEqual((r['unsettled_weekly_rest_hours'],r['total_amount']),(0,415))
        self.assertEqual(sum(x['hours'] for x in r['lines'] if x['component']=='Horas Extras 100%'),2)


if __name__=='__main__':unittest.main()
