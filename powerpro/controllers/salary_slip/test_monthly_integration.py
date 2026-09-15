"""Explicit DEV-only integration tests; runner must roll back the enclosing transaction.

Run with unittest after frappe.init/connect on an authorized development site.
No commits, mails, migrations, or payroll emails are needed.
"""

import json
import os
import uuid
import unittest
from unittest.mock import patch

import frappe

from powerpro.controllers.salary_slip import monthly
from powerpro.controllers.payroll_preflight import _comparison
from powerpro.payroll_rules.monthly_settlement import money
from powerpro.payroll_rules.dominican_republic import calculate_monthly_isr


@unittest.skipUnless(os.environ.get("POWERPRO_MONTHLY_DEV_INTEGRATION") == "1", "Explicit authorized DEV integration run only")
class MonthlyIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.savepoint = "pp_monthly_test"
        frappe.db.savepoint(self.savepoint)
        self.token = "PP-MONTHLY-TEST-" + uuid.uuid4().hex[:8]
        self.structure = frappe.get_doc("Salary Structure", "General Quincenal")
        self.company = self.structure.company
        self.flags = (frappe.flags.via_payroll_entry, frappe.flags.in_test)
        self.addCleanup(self.cleanup)
        frappe.flags.via_payroll_entry = True
        frappe.flags.in_test = True
        self.settings = frappe.get_single("DGII Payroll Settings")
        self.settings.enable_monthly_settlement = 1
        self.settings.monthly_settlement_from_date = "2026-09-01"
        self.settings.save(ignore_permissions=True)
        self.holidays = frappe.get_doc({"doctype": "Holiday List", "holiday_list_name": self.token,
            "from_date": "2026-01-01", "to_date": "2026-12-31"}).insert()
        self.employee = self.make_employee()
        self.assignment(self.employee, "2026-09-01", 40000)

    def cleanup(self):
        frappe.db.rollback(save_point=self.savepoint)
        frappe.flags.via_payroll_entry, frappe.flags.in_test = self.flags
        frappe.clear_cache(doctype="DGII Payroll Settings")

    def make_employee(self, joining="2026-09-01"):
        return frappe.get_doc({"doctype": "Employee", "first_name": self.token + "-" + uuid.uuid4().hex[:4],
            "employee_number": str(uuid.uuid4().int)[:10],
            "gender": "Male", "date_of_birth": "1990-01-01", "date_of_joining": joining,
            "company": self.company, "status": "Active", "holiday_list": self.holidays.name,
            "naming_series": "HR-EMP-", "dependents": 0}).insert()

    def assignment(self, employee, date, base):
        return frappe.get_doc({"doctype": "Salary Structure Assignment", "employee": employee.name,
            "salary_structure": self.structure.name, "from_date": date, "base": base,
            "company": self.company, "currency": "DOP"}).insert().submit()

    def commission(self, amount, day, employee=None):
        return frappe.get_doc({"doctype": "Additional Salary", "employee": (employee or self.employee).name,
            "salary_component": "Comisiones en Venta", "amount": amount, "payroll_date": day,
            "company": self.company, "currency": "DOP", "overwrite_salary_structure_amount": 0}).insert().submit()

    def slip(self, start, end, employee=None, save=True, legacy=False):
        doc = frappe.get_doc({"doctype": "Salary Slip", "employee": (employee or self.employee).name,
            "company": self.company, "start_date": start, "end_date": end, "posting_date": end,
            "payroll_frequency": self.structure.payroll_frequency, "salary_structure": self.structure.name,
            "currency": "DOP", "exchange_rate": 1, "salary_slip_based_on_timesheet": 0})
        doc._pp_force_legacy = legacy
        if save:
            return doc.insert()
        doc.get_emp_and_working_day_details()
        doc.calculate_net_pay()
        return doc

    def exclude_structure(self, name=None):
        self.settings.append("employer_contribution_exclusions", {
            "salary_structure": name or self.structure.name,
        })
        self.settings.save(ignore_permissions=True)

    def employer_totals(self, *slips):
        entry = frappe.new_doc("Payroll Entry")
        entry.company = self.company
        entry.cost_center = frappe.db.get_value("Company", self.company, "cost_center")
        with patch.object(entry, "get_sal_slip_list", return_value=[frappe._dict(name=s.name) for s in slips]), \
             patch.object(entry, "get_payroll_cost_centers_for_employee", return_value={entry.cost_center: 100}):
            return entry._get_dedicated_employer_contribution_totals()

    def employee_amounts(self, slip):
        return (slip.gross_pay, slip.total_deduction, slip.net_pay,
                [(r.salary_component, r.amount) for r in slip.deductions])

    def test_employer_exclusion_monthly_recalculation_submission_and_mixed_accounting(self):
        self.slip("2026-09-01", "2026-09-15").submit()
        close = self.slip("2026-09-16", "2026-09-30")
        baseline = self.employee_amounts(close)
        snapshot_before = json.loads(close.monthly_settlement_snapshot)
        self.assertEqual(len(close.employer_contributions), 4)
        self.exclude_structure()
        close.save()
        self.assertEqual(self.employee_amounts(close), baseline)
        self.assertEqual(close.employer_contributions_excluded, 1)
        self.assertEqual(close.employer_contributions, [])
        snapshot = json.loads(close.monthly_settlement_snapshot)
        self.assertEqual(snapshot["employer"], [])
        self.assertTrue(snapshot["employer_excluded"])
        self.assertEqual(snapshot["employee"], snapshot_before["employee"])
        close.submit()
        self.assertEqual(self.employer_totals(close), ({}, {}))
        # Removing the setting must not change accounting for this submitted slip.
        self.settings.set("employer_contribution_exclusions", [])
        self.settings.save(ignore_permissions=True)
        stored = frappe.get_doc("Salary Slip", close.name)
        self.assertEqual(stored.employer_contributions_excluded, 1)
        self.assertEqual(self.employer_totals(stored), ({}, {}))
        other = self.make_employee()
        self.assignment(other, "2026-09-01", 40000)
        self.slip("2026-09-01", "2026-09-15", other).submit()
        regular = self.slip("2026-09-16", "2026-09-30", other).submit()
        self.assertEqual(len(regular.employer_contributions), 4)
        self.assertEqual(regular.employer_contributions_excluded, 0)
        self.assertEqual(self.employer_totals(stored, regular), self.employer_totals(regular))
        # Adding the setting does not remove historical obligations either.
        self.exclude_structure()
        self.assertEqual(self.employer_totals(regular), self.employer_totals(stored, regular))

    def test_employer_exclusion_iguala_copy_preserves_employee_deductions(self):
        # The real DEV General Iguala is cancelled; never alter it for a test.
        original = frappe.get_doc("Salary Structure", "General Iguala")
        self.structure = frappe.copy_doc(original)
        self.structure.docstatus = 0
        self.structure.name = self.token + "-Iguala"
        self.structure.salary_structure = self.structure.name
        self.structure.is_active = "Yes"
        self.structure.insert().submit()
        self.employee = self.make_employee()
        self.assignment(self.employee, "2026-09-01", 40000)
        baseline = self.slip("2026-09-01", "2026-09-30", save=False)
        self.assertEqual(len(baseline.employer_contributions), 4)
        self.assertIsNone(baseline._pp_monthly)
        self.exclude_structure()
        excluded = self.slip("2026-09-01", "2026-09-30")
        self.assertEqual(self.employee_amounts(excluded), self.employee_amounts(baseline))
        self.assertEqual(excluded.employer_contributions_excluded, 1)
        self.assertEqual(excluded.employer_contributions, [])
        excluded.submit()
        self.assertEqual(self.employer_totals(excluded), ({}, {}))
        self.assertEqual(frappe.db.get_value("Salary Structure", original.name, "docstatus"), 2)

    def test_employer_exclusion_first_half_and_removal_on_draft(self):
        self.exclude_structure()
        first = self.slip("2026-09-01", "2026-09-15").submit()
        self.assertEqual(first.employer_contributions, [])
        close = self.slip("2026-09-16", "2026-09-30")
        baseline = self.employee_amounts(close)
        self.settings.set("employer_contribution_exclusions", [])
        self.settings.save(ignore_permissions=True)
        close.save()
        self.assertEqual(close.employer_contributions_excluded, 0)
        self.assertEqual(len(close.employer_contributions), 4)
        self.assertEqual(self.employee_amounts(close), baseline)

    def test_employer_exclusion_rejects_stale_rows_and_legacy_employer_components(self):
        from powerpro.controllers.salary_slip.helper import validate_employer_contributions
        close = self.slip("2026-09-16", "2026-09-30", save=False)
        close.employer_contributions_excluded = 1
        with self.assertRaises(frappe.ValidationError):
            validate_employer_contributions(close)
        close.set("employer_contributions", [])
        close.append("deductions", {"salary_component": "AFP Empleador", "amount": 10})
        with self.assertRaises(frappe.ValidationError):
            validate_employer_contributions(close)

    def test_real_hrms_raise_commissions_replay_and_accounting(self):
        self.commission(5000, "2026-09-15")
        first = self.slip("2026-09-01", "2026-09-15").submit()
        self.assignment(self.employee, "2026-09-16", 50000)
        self.commission(3000, "2026-09-30")
        self.commission(4000, "2026-09-30")
        close = self.slip("2026-09-16", "2026-09-30")
        snapshot = json.loads(close.monthly_settlement_snapshot)
        self.assertEqual(snapshot["issues"], [])
        self.assertEqual(money(snapshot["taxable_earnings"]), money(57000))
        self.assertEqual(money(snapshot["current"]["COM"]), money(7000))
        self.assertEqual(money(snapshot["previous"]["COM"]), money(5000))
        self.assertEqual(snapshot["sources"][0]["name"], first.name)
        self.assertEqual(money(close.gross_pay), money(32000))
        self.assertEqual(len(close.employer_contributions), 4)
        self.assertEqual(money(close.total_deduction), sum(money(r.amount) for r in close.deductions if not r.do_not_include_in_total))
        legacy = self.slip("2026-09-16", "2026-09-30", save=False, legacy=True)
        comparison = _comparison(legacy, close)
        self.assertEqual(comparison["AFP"]["after"], 1635.9)
        self.assertNotEqual(comparison["employer_AFP"]["before"], comparison["employer_AFP"]["after"])
        before = (close.net_pay, close.monthly_settlement_snapshot)
        close.calculate_net_pay()
        self.assertEqual((close.net_pay, close.monthly_settlement_snapshot), before)
        close.submit()
        stored = frappe.get_doc("Salary Slip", close.name)
        self.assertEqual(stored.monthly_settlement_snapshot, close.monthly_settlement_snapshot)
        entry = frappe.new_doc("Payroll Entry")
        entry.company = self.company
        entry.cost_center = frappe.db.get_value("Company", self.company, "cost_center")
        with patch.object(entry, "get_sal_slip_list", return_value=[frappe._dict(name=close.name)]), \
             patch.object(entry, "get_payroll_cost_centers_for_employee", return_value={entry.cost_center: 100}):
            debit, credit = entry._get_dedicated_employer_contribution_totals()
        expected = sum(money(r.amount) for r in close.employer_contributions)
        self.assertEqual(money(sum(debit.values())), expected)
        self.assertEqual(money(sum(credit.values())), expected)
        journal = frappe.get_doc({"doctype": "Journal Entry", "voucher_type": "Journal Entry",
            "company": self.company, "posting_date": "2026-09-30", "user_remark": self.token})
        for entries, field in ((debit, "debit_in_account_currency"), (credit, "credit_in_account_currency")):
            for (account, cost_center), amount in entries.items():
                journal.append("accounts", {"account": account, "cost_center": cost_center,
                                            "exchange_rate": 1, field: amount})
        journal.insert().submit()
        ledger = frappe.db.sql("select sum(debit),sum(credit) from `tabGL Entry` where voucher_type='Journal Entry' and voucher_no=%s", journal.name)[0]
        self.assertEqual(tuple(money(x) for x in ledger), (expected, expected))
        with self.assertRaises(frappe.ValidationError):
            first.cancel()
        print("MONTHLY_COMPARISON", json.dumps(comparison, sort_keys=True))

    def test_missing_prior_draft_preview_and_submit_block(self):
        first = self.slip("2026-09-01", "2026-09-15")
        close = self.slip("2026-09-16", "2026-09-30")
        self.assertEqual(json.loads(close.monthly_settlement_snapshot)["status"], "incomplete")
        with self.assertRaises(frappe.ValidationError):
            close.submit()
        self.assertEqual(frappe.db.get_value("Salary Slip", first.name, "docstatus"), 0)

    def new_taxable_component(self):
        return frappe.get_doc({"doctype": "Salary Component",
            "salary_component": self.token + "-New taxable income",
            "salary_component_abbr": "ORC" + uuid.uuid4().hex[:6], "type": "Earning",
            "is_tax_applicable": 1, "depends_on_payment_days": 0}).insert()

    def additional_income(self, component, amount, day):
        return frappe.get_doc({"doctype": "Additional Salary", "employee": self.employee.name,
            "salary_component": component.name, "amount": amount, "payroll_date": day,
            "company": self.company, "currency": "DOP", "overwrite_salary_structure_amount": 0}).insert().submit()

    def test_new_component_current_prior_multiple_payments_and_submission(self):
        component = self.new_taxable_component()
        abbr = component.salary_component_abbr
        self.additional_income(component, 50000, "2026-09-15")
        first = self.slip("2026-09-01", "2026-09-15").submit()
        first_snapshot = json.loads(first.monthly_settlement_snapshot)
        self.assertEqual(first_snapshot["issues"], [])
        self.assertEqual(money(first_snapshot["taxable_earnings"]), money(70000))
        self.assertEqual(first_snapshot["employee_applied"], {"AFP": 0, "ARS": 0, "ISRM": 0})
        self.additional_income(component, 12000, "2026-09-30")
        self.additional_income(component, 3000, "2026-09-30")
        close = self.slip("2026-09-16", "2026-09-30")
        snapshot = json.loads(close.monthly_settlement_snapshot)
        self.assertEqual(snapshot["issues"], [])
        self.assertEqual(money(snapshot["taxable_earnings"]), money(105000))
        self.assertEqual(money(snapshot["current_taxable"][abbr]), money(15000))
        self.assertEqual(money(snapshot["previous_taxable"][abbr]), money(50000))
        self.assertEqual(money(snapshot["cotizable"]), money(40000))
        self.assertEqual(money(snapshot["employee"]["AFP"]["amount"]), money(1148))
        self.assertEqual(money(snapshot["employee"]["ARS"]["amount"]), money(1216))
        self.assertEqual(money(snapshot["income_tax_base"]), money(102636))
        self.assertEqual(money(next(r.amount for r in close.deductions if r.abbr == "ISRM")),
                         calculate_monthly_isr(102636, "2026-09-30"))
        amounts = {r.contribution_code: money(r.amount) for r in close.employer_contributions}
        self.assertEqual(amounts, {"AFP": money(2840), "ARS": money(2836), "INFOTEP": money(400), "SRL": money(480)})
        before = (close.net_pay, close.monthly_settlement_snapshot)
        close.calculate_net_pay()
        self.assertEqual((close.net_pay, close.monthly_settlement_snapshot), before)
        close.submit()
        self.assertEqual(close.docstatus, 1)

    def test_prior_tax_flag_preserved_when_component_master_changes(self):
        component = self.new_taxable_component()
        abbr = component.salary_component_abbr
        self.additional_income(component, 50000, "2026-09-15")
        self.slip("2026-09-01", "2026-09-15").submit()
        component.is_tax_applicable = 0
        component.save()
        # HRMS caches get_salary_component_data for a request. A real later
        # request starts with a fresh DB value cache after editing the master.
        frappe.db.value_cache.clear()
        self.additional_income(component, 10000, "2026-09-30")
        close = self.slip("2026-09-16", "2026-09-30").submit()
        snapshot = json.loads(close.monthly_settlement_snapshot)
        self.assertEqual(money(snapshot["previous_taxable"][abbr]), money(50000))
        self.assertNotIn(abbr, snapshot["current_taxable"])
        self.assertEqual(money(snapshot["taxable_earnings"]), money(90000))

    def test_new_employee_needs_no_first_half(self):
        other = self.make_employee("2026-09-16")
        self.assignment(other, "2026-09-16", 40000)
        close = self.slip("2026-09-16", "2026-09-30", other).submit()
        self.assertEqual(money(json.loads(close.monthly_settlement_snapshot)["salary"]), money(20000))

    def test_employee_isolation_and_cancelled_prior(self):
        other = self.make_employee()
        self.assignment(other, "2026-09-01", 40000)
        self.slip("2026-09-01", "2026-09-15", other).submit()
        first = self.slip("2026-09-01", "2026-09-15").submit()
        first.cancel()
        close = self.slip("2026-09-16", "2026-09-30")
        snapshot = json.loads(close.monthly_settlement_snapshot)
        self.assertEqual(snapshot["sources"], [])
        self.assertEqual(snapshot["status"], "incomplete")

    def test_feature_off_matches_baseline_and_retains_proration_flags(self):
        first = self.slip("2026-09-01", "2026-09-15").submit()
        close = self.slip("2026-09-16", "2026-09-30", save=False)
        self.settings.enable_monthly_settlement = 0
        self.settings.save(ignore_permissions=True)
        close.calculate_net_pay()
        reference = self.slip("2026-09-16", "2026-09-30", save=False, legacy=True)
        self.assertEqual(close.net_pay, reference.net_pay)
        self.assertFalse(close.monthly_settlement_snapshot)
        self.assertEqual(frappe.db.get_value("Salary Slip", first.name, "docstatus"), 1)

    def test_revalidate_histories_and_lock_before_submit(self):
        first = self.slip("2026-09-01", "2026-09-15").submit()
        close = self.slip("2026-09-16", "2026-09-30")
        self.assertEqual(json.loads(close.monthly_settlement_snapshot)["status"], "ready")
        first.cancel()
        with self.assertRaises(frappe.ValidationError):
            monthly.before_submit(close)
        self.assertTrue(close._pp_monthly_locked)

    def test_close_blocks_duplicate_through_server_adapter(self):
        self.slip("2026-09-01", "2026-09-15").submit()
        self.slip("2026-09-16", "2026-09-30").submit()
        candidate = self.slip("2026-09-16", "2026-09-30", save=False)
        with self.assertRaises(frappe.ValidationError):
            monthly.before_submit(candidate)

    def test_prorated_current_rows_used_once(self):
        self.slip("2026-09-01", "2026-09-15").submit()
        close = self.slip("2026-09-16", "2026-09-30", save=False)
        base = next(r for r in close.earnings if r.abbr == "B")
        base.amount = 10000  # already prorated income at the adapter boundary
        monthly.prepare(close)
        self.assertEqual(close._pp_monthly["calculation"]["salary"], money(30000))

    def test_database_serializes_two_connections(self):
        import pymysql
        candidate = self.slip("2026-09-01", "2026-09-15", save=False)
        monthly.lock_employee(candidate)
        connection = frappe.db.get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("set session innodb_lock_wait_timeout=1")
                with self.assertRaises(pymysql.err.OperationalError) as error:
                    cursor.execute("select name from `tabEmployee` where name=%s for update", self.employee.name)
                self.assertEqual(error.exception.args[0], 1205)
        finally:
            connection.rollback()
            connection.close()

    def test_replacement_after_cancel_uses_only_confirmed_version(self):
        original = self.slip("2026-09-01", "2026-09-15").submit()
        original.cancel()
        replacement = self.slip("2026-09-01", "2026-09-15")
        replacement.amended_from = original.name
        replacement.save().submit()
        close = self.slip("2026-09-16", "2026-09-30").submit()
        sources = json.loads(close.monthly_settlement_snapshot)["sources"]
        self.assertEqual([s["name"] for s in sources], [replacement.name])

    def test_no_double_proration_through_real_hrms(self):
        self.slip("2026-09-01", "2026-09-15").submit()
        close = self.slip("2026-09-16", "2026-09-30", save=False)
        close.payment_days = 7.5
        close.calculate_net_pay()
        snapshot = json.loads(close.monthly_settlement_snapshot)
        self.assertEqual(money(snapshot["salary"]), money(30000))
        self.assertEqual(money(snapshot["employee"]["AFP"]["amount"]), money(861))
        self.assertEqual(money(snapshot["employee"]["ARS"]["amount"]), money(912))
        self.assertEqual(money(next(r.amount for r in close.deductions if r.abbr == "ARS")), money(912))

    def test_monthly_frequency_uses_actual_full_month_once(self):
        structure = frappe.copy_doc(self.structure)
        structure.name = self.token + "-Monthly"
        structure.payroll_frequency = "Monthly"
        structure.insert().submit()
        self.structure = structure
        backup = json.loads(self.settings.monthly_settlement_backup)
        backup["structures"][structure.name] = {}
        self.settings.monthly_settlement_backup = json.dumps(backup)
        self.settings.save(ignore_permissions=True)
        employee = self.make_employee()
        self.assignment(employee, "2026-09-01", 50000)
        close = self.slip("2026-09-01", "2026-09-30", employee).submit()
        snapshot = json.loads(close.monthly_settlement_snapshot)
        self.assertEqual(money(snapshot["salary"]), money(50000))
        self.assertEqual(snapshot["sources"], [])
        self.assertTrue(snapshot["close"])
