import unittest
from datetime import date
from decimal import Decimal

from powerpro.payroll_rules.dominican_republic import (
    calculate_infotep_employer,
    calculate_monthly_isr,
    calculate_srl_employer,
    get_isr_scale,
    get_tss_rule,
)


class DominicanPayrollRulesTest(unittest.TestCase):
    def test_2025_tss_boundaries(self):
        self.assertEqual(get_tss_rule(date(2025, 3, 31)).pension_ceiling, Decimal("387050.00"))
        self.assertEqual(get_tss_rule(date(2025, 4, 1)).pension_ceiling, Decimal("433496.00"))

    def test_2026_tss_boundary(self):
        rule = get_tss_rule(date(2026, 2, 1))
        self.assertEqual(rule.srl_ceiling, Decimal("92892.00"))
        self.assertEqual(rule.sfs_ceiling, Decimal("232230.00"))
        self.assertEqual(rule.pension_ceiling, Decimal("464460.00"))

    def test_2025_and_2026_isr_scales_are_equal(self):
        scale_2025 = get_isr_scale(date(2025, 7, 31))
        scale_2026 = get_isr_scale(date(2026, 7, 31))
        self.assertEqual(scale_2025.exempt_through, scale_2026.exempt_through)
        self.assertEqual(scale_2025.fourth_rate, scale_2026.fourth_rate)

    def test_monthly_isr_examples(self):
        self.assertEqual(calculate_monthly_isr("34685.00", date(2025, 7, 31)), Decimal("0.00"))
        self.assertEqual(calculate_monthly_isr("50000.00", date(2025, 7, 31)), Decimal("2297.25"))
        self.assertEqual(calculate_monthly_isr("71545.00", date(2025, 7, 31)), Decimal("6504.85"))

    def test_isr_regression_for_june_2026_payroll(self):
        cases = {
            "47045.00": Decimal("1854.00"),
            "70567.50": Decimal("6309.35"),
            "39988.25": Decimal("795.49"),
            "37636.00": Decimal("442.65"),
        }
        for monthly_taxable_income, expected in cases.items():
            with self.subTest(monthly_taxable_income=monthly_taxable_income):
                self.assertEqual(
                    calculate_monthly_isr(monthly_taxable_income, date(2026, 6, 30)),
                    expected,
                )

    def test_infotep_employer_uses_salary_and_commissions(self):
        self.assertEqual(calculate_infotep_employer("50000.00"), Decimal("500.00"))
        self.assertEqual(calculate_infotep_employer("50000.00", "10000.00"), Decimal("600.00"))

    def test_srl_employer_uses_2026_ceiling(self):
        self.assertEqual(
            calculate_srl_employer("50000.00", date(2026, 8, 31)),
            Decimal("600.00"),
        )
        self.assertEqual(
            calculate_srl_employer("150000.00", date(2026, 8, 31)),
            Decimal("1114.70"),
        )


if __name__ == "__main__":
    unittest.main()
