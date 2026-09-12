import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def load_rule(name):
    spec = spec_from_file_location(name, Path(__file__).resolve().parents[1] / 'powerpro' / 'payroll_rules' / (name + '.py'))
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


combined = load_rule('overtime_combined_day')
REVIEW, SINGLE, ADDITIVE, FIELD, HOURS = (combined.REVIEW, combined.SINGLE, combined.ADDITIVE, combined.FIELD, combined.HOURS)
cash_kwargs, settlement_blocker = combined.cash_kwargs, combined.settlement_blocker
calculate_cash_settlement = load_rule('overtime_cash_settlement').calculate_cash_settlement


class CombinedDayTest(unittest.TestCase):
    def calc(self, mode=SINGLE, covered=0, rest=100):
        policy={FIELD:mode,'extraordinary_percent':100,'weekly_rest_percent':rest}
        return calculate_cash_settlement(hourly_rate=100,holiday_100_hours=1,night_hours=1,
            holiday_base_covered_hours=covered,**cash_kwargs(policy,{HOURS:1}))

    def test_single_and_additive_only_one_base(self):
        for mode,covered,expected in [(SINGLE,0,215),(SINGLE,1,115),(ADDITIVE,0,315),(ADDITIVE,1,215),(ADDITIVE,.5,265)]:
            self.assertEqual(self.calc(mode,covered)['total_amount'],expected)

    def test_single_uses_larger_premium(self):
        self.assertEqual(self.calc(rest=150)['total_amount'],265)
        self.assertEqual(self.calc(ADDITIVE,rest=150)['total_amount'],365)

    def test_only_joint_segments_receive_supplement(self):
        calculation={'segments':[{'classification':'Legal Holiday','verified_hours':2},
            {'classification':'Legal Holiday on Weekly Rest','verified_hours':.5}]}
        args=cash_kwargs({FIELD:ADDITIVE,'extraordinary_percent':100,'weekly_rest_percent':100},calculation)
        self.assertEqual(args[HOURS],.5)
        result=calculate_cash_settlement(hourly_rate=100,holiday_100_hours=2.5,**args)
        self.assertEqual(result['total_amount'],550)

    def test_unconfigured_and_invalid_values_fail(self):
        for mode in [None,REVIEW,'unknown']:
            with self.assertRaises(ValueError):cash_kwargs({FIELD:mode},{HOURS:1})
        for hours in [-1,float('nan'),float('inf')]:
            with self.assertRaises(ValueError):self.calc_with_hours(hours)
        with self.assertRaises(ValueError):calculate_cash_settlement(hourly_rate=100,holiday_100_hours=1,holiday_weekly_rest_hours=2,holiday_weekly_rest_percent=200)

    def calc_with_hours(self,hours):
        return cash_kwargs({FIELD:ADDITIVE,'extraordinary_percent':100,'weekly_rest_percent':100},{HOURS:hours})

    def test_compensatory_does_not_erase_cash_obligation(self):
        p={FIELD:SINGLE,'extraordinary_percent':100,'weekly_rest_percent':100}
        self.assertIsNotNone(settlement_blocker(p,{HOURS:1},'Compensatory Rest'))
        self.assertIsNone(settlement_blocker(p,{HOURS:1},'Cash'))
        self.assertEqual(cash_kwargs(p,{}),{})
