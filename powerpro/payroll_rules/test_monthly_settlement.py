from copy import deepcopy
from decimal import Decimal
from unittest import TestCase

from .monthly_settlement import calculate, money, month_bounds, period_issues, taxable_amounts
from .dominican_republic import calculate_monthly_isr


class MonthlyArithmeticTest(TestCase):
    def calc(self, current=None, previous=None, deductions=None, employer=None, **kwargs):
        return calculate(current or {}, previous or {}, deductions or {}, employer or {}, "2026-09-30", **kwargs)

    def test_raise_and_different_commissions(self):
        r = self.calc({"B": 25000, "COM": 7000}, {"B": 20000, "COM": 5000})
        self.assertEqual(r["taxable_earnings"], money(57000))
        self.assertEqual(r["salary"], money(45000))
        self.assertEqual(r["employee"]["AFP"]["amount"], money(1635.9))
        self.assertEqual(r["employee"]["ARS"]["amount"], money(1732.8))
        employer = {r["code"]: r for r in r["employer"]}
        self.assertEqual(employer["AFP"]["amount"], money(4047))
        self.assertEqual(employer["ARS"]["amount"], money(4041.3))
        self.assertEqual(employer["INFOTEP"]["amount"], money(570))
        self.assertEqual(employer["SRL"]["amount"], money(684))

    def test_equal_commissions_missing_current_and_no_commission(self):
        for before, after, expected in ((5000, 5000, 10000), (5000, 0, 5000), (0, 0, 0)):
            with self.subTest(before=before, after=after):
                self.assertEqual(self.calc({"COM": after}, {"COM": before})["totals"]["COM"], money(expected))

    def test_partial_salary_is_not_doubled_or_prorated_again(self):
        self.assertEqual(self.calc({"B": 6000}, {"B": 9000})["salary"], money(15000))
        self.assertEqual(self.calc({"B": 6000})["salary"], money(6000))

    def test_statistical_and_employer_components_not_taxable(self):
        r = self.calc({"B": 20000, "BAM": 40000, "MIMP": 60000, "GAFP": 2840, "RPA": 10000})
        self.assertEqual(r["taxable_earnings"], money(20000))

    def test_vacation_overtime_and_bonus_have_distinct_bases(self):
        r = self.calc({"B": 50000, "COM": 2500, "VAC": 1000, "HE": 3000, "BNF": 4000})
        self.assertEqual(r["cotizable"], money(53500))
        self.assertEqual(r["taxable_earnings"], money(60500))
        self.assertEqual(next(x for x in r["employer"] if x["code"] == "INFOTEP")["base_amount"], money(52500))

    def test_all_tss_ceilings(self):
        r = self.calc({"B": 500000}, {"COM": 100000})
        self.assertEqual(r["afp_base"], money(464460))
        self.assertEqual(r["ars_base"], money(232230))
        rows = {x["code"]: x for x in r["employer"]}
        self.assertEqual(rows["AFP"]["base_amount"], money(464460))
        self.assertEqual(rows["ARS"]["base_amount"], money(232230))
        self.assertEqual(rows["SRL"]["base_amount"], money(92892))

    def test_prior_withholdings_and_dependents(self):
        r = self.calc({"B": 60000}, deductions={"AFP": 100, "ARS": 50, "ISRM": 20, "DP": 100}, dependents=200)
        self.assertEqual(r["employee"]["AFP"]["balance"], money(1722 - 100))
        self.assertEqual(r["income_tax_base"], money(60000 - 1722 - 1824 - 300))
        self.assertEqual(r["employee"]["ISRM"]["balance"], calculate_monthly_isr(r["income_tax_base"], "2026-09-30") - 20)

    def test_prior_employer_amounts_subtracted(self):
        r = self.calc({"B": 50000}, employer={"AFP": 1000})
        self.assertEqual(next(x for x in r["employer"] if x["code"] == "AFP")["amount"], money(2550))

    def test_negative_balances_are_blockers_not_refunds(self):
        r = self.calc({"B": 1000}, deductions={"AFP": 100, "ISRM": 100}, employer={"AFP": 100})
        self.assertEqual(len(r["issues"]), 3)
        self.assertEqual(r["employee"]["AFP"]["amount"], 0)
        self.assertLess(r["employee"]["AFP"]["balance"], 0)

    def test_isr_boundaries_use_versioned_rule(self):
        for monthly in (0, 34685, 52027.42, 72260.25, 100000):
            r = self.calc({"B": monthly}, employee_afp_rate=0, employee_ars_rate=0)
            self.assertEqual(r["employee"]["ISRM"]["total"], calculate_monthly_isr(monthly, "2026-09-30"))

    def test_idempotent_without_mutating_inputs(self):
        data = {"B": Decimal("12345.67"), "COM": Decimal("123.45")}
        original = deepcopy(data)
        self.assertEqual(self.calc(data), self.calc(data))
        self.assertEqual(data, original)

    def test_future_year_requires_verified_scale(self):
        with self.assertRaises(ValueError):
            calculate({"B": 50000}, {}, {}, {}, "2027-01-31")


class MonthlyTaxableComponentsTest(TestCase):
    def test_new_taxable_component_from_both_halves_changes_only_isr(self):
        current = {"B": 25000, "ORC": 7000}
        previous = {"B": 25000, "ORC": 50000}
        result = calculate(current, previous, {}, {}, "2026-08-31",
                           current_taxable=current, previous_taxable=previous)
        baseline = calculate(current, previous, {}, {}, "2026-08-31")
        self.assertEqual(result["taxable_earnings"], money(107000))
        self.assertEqual(result["cotizable"], money(50000))
        self.assertEqual(result["employee"]["AFP"], baseline["employee"]["AFP"])
        self.assertEqual(result["employee"]["ARS"], baseline["employee"]["ARS"])
        self.assertEqual(result["employer"], baseline["employer"])
        self.assertEqual(result["income_tax_base"], money(104045))
        self.assertEqual(result["employee"]["ISRM"]["total"],
                         calculate_monthly_isr(104045, "2026-08-31"))

    def test_row_flags_duplicates_statistical_and_legacy_rows(self):
        rows = [
            {"abbr": "B", "amount": 25000},  # historical flag absent
            {"abbr": "ORC", "amount": 5000, "is_tax_applicable": 1},
            {"abbr": "ORC", "amount": 7000, "is_tax_applicable": 1},
            {"abbr": "ORC", "amount": 9000, "is_tax_applicable": 0},
            {"abbr": "NEW", "amount": 2000, "is_tax_applicable": 1},
            {"abbr": "REIMBURSE", "amount": 8000, "is_tax_applicable": 0},
            {"abbr": "STAT", "amount": 99999, "is_tax_applicable": 1,
             "do_not_include_in_total": 1},
        ]
        original = deepcopy(rows)
        self.assertEqual(taxable_amounts(rows), {"B": money(25000), "ORC": money(12000), "NEW": money(2000)})
        self.assertEqual(taxable_amounts(rows), taxable_amounts(rows))
        self.assertEqual(rows, original)

    def test_explicit_empty_taxable_map_and_prior_only_custom_payment(self):
        result = calculate({"ORC": 9000}, {"ORC": 50000}, {"ISRM": 100}, {}, "2026-08-31",
                           current_taxable={}, previous_taxable={"ORC": 50000})
        self.assertEqual(result["taxable_earnings"], money(50000))
        self.assertEqual(result["current_taxable"], {})
        self.assertEqual(result["employee"]["ISRM"]["amount"], calculate_monthly_isr(50000, "2026-08-31") - 100)


class MonthlyPeriodTest(TestCase):
    def current(self, start="2026-09-16", end="2026-09-30", frequency="Bimonthly"):
        return {"start_date": start, "end_date": end, "payroll_frequency": frequency}

    def prior(self, status=1, **kwargs):
        return {"name": "TEST-FIRST", "start_date": "2026-09-01", "end_date": "2026-09-15", "docstatus": status, **kwargs}

    def test_confirmed_prior_satisfies_coverage(self):
        self.assertEqual(period_issues(self.current(), [self.prior()]), [])

    def test_missing_draft_and_cancelled_prior_do_not_satisfy_coverage(self):
        for history in ([], [self.prior(0)], [self.prior(2)]):
            self.assertTrue(any("Falta" in x for x in period_issues(self.current(), history)))

    def test_new_employee_does_not_require_preemployment_slip(self):
        self.assertEqual(period_issues(self.current(), [], "2026-09-16"), [])

    def test_first_half_does_not_require_future_slip(self):
        self.assertEqual(period_issues(self.current("2026-09-01", "2026-09-15"), []), [])

    def test_month_lengths(self):
        for end in ("2025-02-28", "2024-02-29", "2026-09-30", "2026-08-31"):
            first, last = month_bounds(end)
            self.assertEqual(str(last), end)
            self.assertEqual(period_issues(self.current(str(first), end, "Monthly"), []), [])

    def test_overlap_and_duplicate_close(self):
        self.assertTrue(period_issues(self.current(), [self.prior(end_date="2026-09-30")]))

    def test_cross_month(self):
        self.assertTrue(period_issues(self.current("2026-08-16"), []))

    def test_early_departure_requires_separate_settlement(self):
        self.assertTrue(period_issues(self.current(), [self.prior()], relieving_date="2026-09-20"))

    def test_unsupported_frequency(self):
        self.assertTrue(period_issues(self.current(frequency="Weekly"), [self.prior()]))
