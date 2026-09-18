"""Read-only report regression tests; runnable without a Frappe database."""

import ast
from datetime import date
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


REPORT = Path(__file__).resolve().parents[1] / "powerpro/power_pro/report/accounts_receivable_reloaded/accounts_receivable_reloaded.py"


def entry(name, voucher_type, amount, day=13, party="Employee A", account="Employee AR"):
    return SimpleNamespace(
        name=name, voucher_type=voucher_type, voucher_no=name,
        against_voucher_type=voucher_type, against_voucher_no=name,
        amount=amount, amount_in_account_currency=amount, party_type="Employee",
        party=party, account=account, account_currency="DOP",
        posting_date=date(2026, 9, day),
    )


def link(row, advance="ADV-1", amount=None):
    return SimpleNamespace(
        voucher_type=row.voucher_type, voucher_no=row.voucher_no,
        against_voucher_type="Employee Advance", against_voucher_no=advance,
        amount=row.amount if amount is None else amount, currency="DOP",
    )


class EmployeeAdvanceReportTests(unittest.TestCase):
    def run_filter(self, entries, links, day=18):
        # Exercise the actual report method with only its database boundary mocked.
        tree = ast.parse(REPORT.read_text())
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef))
        method = next(node for node in cls.body if getattr(node, "name", "") == "exclude_settled_employee_advance_entries")
        db = Mock(return_value=links)
        namespace = {"frappe": SimpleNamespace(get_all=db), "flt": float, "getdate": lambda value: value}
        exec(compile(ast.Module(body=[method], type_ignores=[]), str(REPORT), "exec"), namespace)
        report = SimpleNamespace(
            ple_entries=entries, currency_precision=2,
            filters=SimpleNamespace(company="Company", report_date=date(2026, 9, day)),
        )
        namespace[method.name](report)
        if db.called:
            self.assertEqual(db.call_args.kwargs["filters"]["delinked"], 0)
            self.assertEqual(db.call_args.kwargs["filters"]["company"], "Company")
        return [row.name for row in report.ple_entries]

    def setUp(self):
        self.payment = entry("PAY-1", "Payment Entry", 10000)
        self.journal = entry("JV-1", "Journal Entry", -10000, day=15)
        self.pair = [self.payment, self.journal]
        self.links = list(map(link, self.pair))

    def test_fully_returned_pair_is_hidden(self):
        self.assertEqual(self.run_filter(self.pair, self.links), [])

    def test_historical_date_keeps_payment(self):
        self.assertEqual(self.run_filter([self.payment], self.links, day=14), ["PAY-1"])

    def test_future_payment_option_cannot_settle_early(self):
        self.assertEqual(self.run_filter(self.pair, self.links, day=14), ["PAY-1", "JV-1"])

    def test_partial_return_remains_visible(self):
        self.journal.amount = self.journal.amount_in_account_currency = -4000
        self.assertEqual(self.run_filter(self.pair, list(map(link, self.pair))), ["PAY-1", "JV-1"])

    def test_unrelated_row_on_same_journal_survives(self):
        other = entry("OTHER", "Journal Entry", -500)
        other.voucher_no = "JV-1"
        other.against_voucher_no = "SINV-1"
        other.against_voucher_type = "Sales Invoice"
        self.assertEqual(self.run_filter(self.pair + [other], self.links), ["OTHER"])

    def test_shared_payroll_with_other_employee_is_preserved(self):
        other = entry("OTHER", "Journal Entry", -500, party="Employee B")
        other.voucher_no = other.against_voucher_no = "JV-1"
        self.assertEqual(self.run_filter(self.pair + [other], self.links), ["PAY-1", "JV-1", "OTHER"])

    def test_extra_unallocated_amount_preserves_both_sides(self):
        self.journal.amount = self.journal.amount_in_account_currency = -11000
        self.assertEqual(self.run_filter(self.pair, self.links), ["PAY-1", "JV-1"])

    def test_cross_account_pair_is_preserved(self):
        self.journal.account = "Other AR"
        self.assertEqual(self.run_filter(self.pair, self.links), ["PAY-1", "JV-1"])

    def test_exchange_difference_is_preserved(self):
        self.journal.amount = -9999
        self.assertEqual(self.run_filter(self.pair, self.links), ["PAY-1", "JV-1"])

    def test_currency_mismatch_is_preserved(self):
        self.links[1].currency = "USD"
        self.assertEqual(self.run_filter(self.pair, self.links), ["PAY-1", "JV-1"])

    def test_unsettled_second_advance_preserves_connected_pair(self):
        self.links.append(link(self.journal, "ADV-2", -500))
        self.assertEqual(self.run_filter(self.pair, self.links), ["PAY-1", "JV-1"])

    def test_customer_is_unchanged(self):
        self.payment.party_type = "Customer"
        self.journal.party_type = "Customer"
        self.assertEqual(self.run_filter(self.pair, self.links), ["PAY-1", "JV-1"])


if __name__ == "__main__":
    unittest.main()
