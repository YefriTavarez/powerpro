import unittest
from decimal import Decimal
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('supplement_rules', Path(__file__).resolve().parents[1] / 'powerpro/supplements/rules.py')
rules = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rules)
applies, key, money, period_amount, resolve = (getattr(rules, name) for name in
    ('applies', 'key', 'money', 'period_amount', 'resolve'))


class SupplementRulesTest(unittest.TestCase):
    def salary(self, name="existing", **kwargs):
        return dict(name=name, amount=1900, docstatus=1, disabled=0, is_recurring=0,
                    payroll_date="2026-09-15", **kwargs)

    def test_monthly_and_halves(self):
        self.assertEqual(period_amount(19720, "Monthly", "2026-09-01", "2026-09-30"), 19720)
        self.assertEqual(period_amount(19720, "Bimonthly", "2026-09-01", "2026-09-15"), 9860)
        self.assertEqual(period_amount(3800, "Bimonthly", "2026-09-16", "2026-09-30"), 1900)

    def test_rounding_reconciles_and_leap_year(self):
        for precision in (2, 4):
            a = period_amount("100.0101", "Bimonthly", "2028-02-01", "2028-02-15", precision=precision)
            b = period_amount("100.0101", "Bimonthly", "2028-02-16", "2028-02-29", precision=precision)
            self.assertEqual(a+b, money("100.0101", precision))

    def test_second_day_15_supported_explicitly(self):
        self.assertEqual(period_amount(3800, "Bimonthly", "2026-09-01", "2026-09-14",15),1900)
        self.assertEqual(period_amount(3800, "Bimonthly", "2026-09-15", "2026-09-30",15),1900)

    def test_unsupported_periods_are_not_silently_prorated(self):
        for freq,start,end in [("Monthly","2026-09-02","2026-09-30"),
            ("Bimonthly","2026-09-01","2026-09-30"),("Weekly","2026-09-01","2026-09-07"),
            ("Monthly","2026-09-01","2026-10-31")]:
            with self.subTest(freq=freq,start=start,end=end), self.assertRaises(ValueError):
                period_amount(3800,freq,start,end)

    def test_invalid_money(self):
        for value in (-1,"NaN","Infinity","garbage"):
            with self.subTest(value=value), self.assertRaises(ValueError):money(value)

    def test_recurrence_matches_hrms_end_date_semantics(self):
        row=dict(name='r',docstatus=1,is_recurring=1,from_date='2026-09-05',to_date='2026-09-15')
        self.assertTrue(applies(row,'2026-09-01','2026-09-15'))
        self.assertFalse(applies(row,'2026-09-01','2026-09-30'))
        self.assertFalse(applies(dict(row,disabled=1),'2026-09-01','2026-09-15'))
        self.assertFalse(applies(dict(row,docstatus=2),'2026-09-01','2026-09-15'))

    def test_matching_amount_does_not_establish_ownership(self):
        with self.assertRaisesRegex(ValueError,'sin clasificar'):resolve(1900,[self.salary()])

    def test_explicit_legacy_coverage_reused(self):
        self.assertEqual(resolve(1900,[self.salary()],coverage_names=['existing']),'existing')

    def test_independent_payment_can_coexist(self):
        self.assertIsNone(resolve(1900,[self.salary()],independent_names=['existing']))
        self.assertEqual(resolve(1900,[self.salary(),self.salary('bonus',pp_supplement_treatment='Independent')],
                                 coverage_names=['existing']),'existing')

    def test_duplicate_coverage_and_amount_mismatch_stop(self):
        with self.assertRaisesRegex(ValueError,'más de un'):resolve(1900,[self.salary(),self.salary('other')],['existing','other'])
        with self.assertRaisesRegex(ValueError,'no coincide'):resolve(3800,[self.salary()],['existing'])
        with self.assertRaisesRegex(ValueError,'no coincide'):resolve(0,[self.salary()],['existing'])

    def test_overwrite_rejected_even_if_independent(self):
        with self.assertRaisesRegex(ValueError,'reemplaza'):resolve(1900,[self.salary(overwrite_salary_structure_amount=1)],independent_names=['existing'])

    def test_stable_identity_and_owned_retries(self):
        identity=key('C','E','incentivo_especial','2026-09-01','2026-09-15')
        self.assertEqual(len(identity),64)
        self.assertNotEqual(identity,key('C','E','asignacion_transporte','2026-09-01','2026-09-15'))
        self.assertEqual(resolve(1900,[self.salary(pp_supplement_key=identity)],owned_key=identity),'existing')


if __name__ == '__main__':unittest.main()
