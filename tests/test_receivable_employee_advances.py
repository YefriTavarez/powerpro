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


SUMMARY_REPORT = REPORT.parent.parent / "accounts_receivable_summary_reloaded/accounts_receivable_summary_reloaded.py"


class AttrDict(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__


class EmployeeAdvanceSummaryTests(unittest.TestCase):
    def run_summary(self, entries, links, day=18):
        tree = ast.parse(SUMMARY_REPORT.read_text())
        report_class = next(node for node in tree.body if isinstance(node, ast.ClassDef))
        # Keep the real summary aggregation, mocking only its framework/provider boundaries.
        report_class.bases = []
        filters = AttrDict(
            company="Company", report_date=date(2026, 9, day), group_by_party=True,
            party_type="Employee", party=["Employee A"], party_account="Employee AR",
        )
        provider = Mock()

        def detail_rows(detail_filters):
            self.assertIsNot(detail_filters, filters)
            self.assertFalse(detail_filters.group_by_party)
            for key in ("company", "report_date", "party_type", "party", "party_account"):
                self.assertEqual(detail_filters[key], filters[key])
            remaining = EmployeeAdvanceReportTests().run_filter(entries, links, day)
            rows = [
                AttrDict(
                    party=row.party, party_type=row.party_type, currency="DOP",
                    invoiced=max(row.amount, 0), paid=max(-row.amount, 0),
                    outstanding=row.amount, range1=row.amount, total_due=row.amount,
                )
                for row in entries if row.name in remaining
            ]
            return SimpleNamespace(run=Mock(return_value=([], rows)))

        provider.side_effect = detail_rows
        namespace = {
            "frappe": SimpleNamespace(_dict=AttrDict),
            "ReloadedReceivablePayableReport": provider,
            "get_igc_settings": lambda: None,
            "get_currency_precision": lambda: 2,
            "get_partywise_advanced_payment_amount": Mock(return_value={}),
            "scrub": str.lower,
            "flt": lambda value, precision=None: round(float(value), precision or 2),
        }
        exec(compile(ast.Module(body=[report_class], type_ignores=[]), str(SUMMARY_REPORT), "exec"), namespace)
        report = namespace[report_class.name]()
        report.filters = filters
        report.party_type = ["Employee"]
        report.party_naming_by = "Employee Name"
        report.account_type = "Receivable"
        args = {"account_type": "Receivable", "naming_by": ["Selling Settings", "cust_master_name"]}
        report.get_data(args)
        provider.assert_called_once()
        self.assertTrue(filters.group_by_party)
        return report.data

    def test_summary_provider_is_powerpro_reloaded(self):
        tree = ast.parse(SUMMARY_REPORT.read_text())
        imports = [
            (node.module, alias.name, alias.asname)
            for node in tree.body if isinstance(node, ast.ImportFrom)
            for alias in node.names
        ]
        self.assertIn((
            "powerpro.power_pro.report.accounts_receivable_reloaded.accounts_receivable_reloaded",
            "ReceivablePayableReport", "ReloadedReceivablePayableReport",
        ), imports)

    def test_settled_pair_does_not_inflate_other_open_advance(self):
        pair = [entry("PAY-1", "Payment Entry", 10000), entry("JV-1", "Journal Entry", -10000, day=15)]
        other = entry("PAY-2", "Payment Entry", 500)
        rows = self.run_summary(pair + [other], list(map(link, pair)))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].invoiced, 500)
        self.assertEqual(rows[0].paid, 0)
        self.assertEqual(rows[0].outstanding, 500)
        self.assertEqual(rows[0].range1, 500)

    def test_settled_only_employee_is_absent(self):
        pair = [entry("PAY-1", "Payment Entry", 10000), entry("JV-1", "Journal Entry", -10000, day=15)]
        self.assertEqual(self.run_summary(pair, list(map(link, pair))), [])

    def test_historical_summary_keeps_open_advance(self):
        payment = entry("PAY-1", "Payment Entry", 10000)
        rows = self.run_summary([payment], [link(payment)], day=14)
        self.assertEqual(rows[0].invoiced, 10000)
        self.assertEqual(rows[0].outstanding, 10000)

    def test_partial_return_stays_in_summary(self):
        pair = [entry("PAY-1", "Payment Entry", 10000), entry("JV-1", "Journal Entry", -4000, day=15)]
        rows = self.run_summary(pair, list(map(link, pair)))
        self.assertEqual(rows[0].invoiced, 10000)
        self.assertEqual(rows[0].paid, 4000)
        self.assertEqual(rows[0].outstanding, 6000)


if __name__ == "__main__":
    unittest.main()
