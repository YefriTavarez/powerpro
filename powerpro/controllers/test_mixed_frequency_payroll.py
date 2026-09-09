"""Read-only contract tests; all framework/database operations are mocked."""
from datetime import date
import importlib.util
from pathlib import Path
from types import ModuleType
from unittest import TestCase
from unittest.mock import Mock, patch

import frappe
from powerpro.controllers import mixed_frequency_payroll as mixed


def row(**values):
    return frappe._dict(values)


class MixedPayrollTest(TestCase):
    def setUp(self):
        self.entry = row(name="PAY-1", docstatus=1, company="IGC", currency="DOP", payroll_payable_account="PAYABLE",
                         payroll_frequency="Bimonthly", start_date="2026-08-16", end_date="2026-08-31",
                         salary_slip_based_on_timesheet=0, posting_date="2026-08-31", exchange_rate=1,
                         employees=[row(employee="M"), row(employee="B")])
        self.settings = row(include_monthly_in_second_quincena=1)
        self.cache = self.start(patch.object(mixed.frappe, "get_cached_doc", side_effect=self.cached))
        self.get_all = self.start(patch.object(mixed.frappe, "get_all"))
        self.start(patch.object(mixed.frappe, "throw", side_effect=ValueError))

    def start(self, context):
        result = context.start()
        self.addCleanup(context.stop)
        return result

    def cached(self, doctype, *args):
        return self.settings if doctype == "DGII Payroll Settings" else self.entry

    def period(self, frequency="Monthly"):
        return row(name="SSA-M", employee="M", salary_structure="Monthly Structure", from_date="2026-08-01",
                   **mixed.salary_period(frequency, self.entry.start_date, self.entry.end_date))

    def slip(self, new=True):
        return row(name=None if new else "SS-1", payroll_entry="PAY-1", employee="M",
                   payroll_frequency="Bimonthly", start_date="2026-08-16", end_date="2026-08-31",
                   is_new=lambda: new)

    def test_default_disabled_and_first_half_do_not_expand_frequency(self):
        self.settings.include_monthly_in_second_quincena = 0
        self.assertEqual(mixed.frequencies(self.entry), ["Bimonthly"])
        self.settings.include_monthly_in_second_quincena = 1
        self.assertEqual(mixed.frequencies(self.entry), ["Bimonthly", "Monthly"])
        self.entry.update(start_date="2026-08-01", end_date="2026-08-15")
        self.assertEqual(mixed.frequencies(self.entry), ["Bimonthly"])

    def test_latest_assignment_does_not_resurrect_old_eligible_contract(self):
        newer = row(employee="M", salary_structure="Weekly", payroll_payable_account="PAYABLE")
        older = row(employee="M", salary_structure="Monthly", payroll_payable_account="PAYABLE")
        self.get_all.side_effect = [[newer, older], [row(name="Monthly", payroll_frequency="Monthly")]]
        self.assertEqual(mixed.assignments(self.entry), {})
        self.assertIn("from_date desc", self.get_all.call_args_list[0].kwargs["order_by"])

    def test_resolver_scopes_company_currency_account_status_and_dates(self):
        self.get_all.side_effect = [
            [row(employee="M", salary_structure="Monthly", payroll_payable_account="PAYABLE"),
             row(employee="B", salary_structure="Bimonthly", payroll_payable_account="WRONG")],
            [row(name="Monthly", payroll_frequency="Monthly"), row(name="Bimonthly", payroll_frequency="Bimonthly")],
        ]
        resolved = mixed.assignments(self.entry, ["M", "B"])
        self.assertEqual(list(resolved), ["M"])
        self.assertEqual(resolved["M"].start_date, date(2026, 8, 1))
        filters = self.get_all.call_args_list[0].kwargs["filters"]
        self.assertEqual(filters["docstatus"], 1)
        self.assertEqual(filters["company"], "IGC")
        self.assertEqual(filters["currency"], "DOP")
        self.assertEqual(filters["from_date"], ["<=", "2026-08-31"])
        self.assertEqual(self.get_all.call_args_list[1].kwargs["filters"]["is_active"], "Yes")

    def test_preview_and_new_slips_receive_full_month_before_calculation(self):
        self.start(patch.object(mixed, "require_assignment", return_value=self.period()))
        slip = self.slip()
        mixed.prepare_slip(slip)
        self.assertEqual(slip.payroll_frequency, "Monthly")
        self.assertEqual(slip.start_date, date(2026, 8, 1))
        self.assertEqual(slip.salary_structure, "Monthly Structure")

    def test_existing_slips_and_disabled_setting_are_not_rewritten(self):
        existing = self.slip(new=False)
        mixed.prepare_slip(existing)
        self.assertEqual(existing.start_date, "2026-08-16")
        self.settings.include_monthly_in_second_quincena = 0
        new = self.slip()
        mixed.prepare_slip(new)
        self.assertEqual(new.start_date, "2026-08-16")

    def test_unselected_employee_is_rejected(self):
        slip = self.slip()
        slip.employee = "UNSELECTED"
        with self.assertRaises(ValueError):
            mixed.prepare_slip(slip)

    def test_overlap_query_includes_drafts_other_entries_and_full_month(self):
        self.get_all.return_value = []
        mixed.overlaps(self.entry, "M", self.period(), exclude="SELF")
        filters = self.get_all.call_args.kwargs["filters"]
        self.assertNotIn("payroll_entry", filters)
        self.assertEqual(filters["docstatus"], ["<", 2])
        self.assertEqual(filters["end_date"], [">=", date(2026, 8, 1)])
        self.assertEqual(filters["name"], ["!=", "SELF"])

    def test_read_scope_preserves_linked_monthly_slips_after_disable(self):
        self.settings.include_monthly_in_second_quincena = 0
        self.start(patch.object(mixed.frappe.db, "exists", return_value=True))
        scoped = mixed.read_scope(self.entry)
        self.assertEqual(scoped.start_date, date(2026, 8, 1))
        self.assertEqual(self.entry.start_date, "2026-08-16")
        self.assertEqual(scoped.name, self.entry.name)

    def test_read_scope_without_monthly_slips_is_unchanged(self):
        self.start(patch.object(mixed.frappe.db, "exists", return_value=False))
        self.assertIs(mixed.read_scope(self.entry), self.entry)

    def test_attendance_uses_each_groups_period(self):
        self.start(patch.object(mixed, "assignments", return_value={
            "M": self.period(), "B": row(payroll_frequency="Bimonthly")}))
        seen = []
        def parent(scoped):
            seen.append((scoped.payroll_frequency, scoped.start_date, [r.employee for r in scoped.employees]))
            return Mock(get_employees_with_unmarked_attendance=Mock(return_value=[]))
        self.assertEqual(mixed.attendance(self.entry, parent), [])
        self.assertEqual(seen, [("Bimonthly", date(2026, 8, 16), ["B"]), ("Monthly", date(2026, 8, 1), ["M"])])
        self.assertEqual(self.entry.start_date, "2026-08-16")
        self.assertEqual(len(self.entry.employees), 2)

    def test_selection_deduplicates_and_excludes_existing_slips_after_resolution(self):
        controller = ModuleType("powerpro.controllers.payroll_entry")
        controller.get_salary_structure = Mock(side_effect=[["Bi"], ["Monthly"]])
        controller.get_filtered_employees = Mock(side_effect=[
            [row(employee="B"), row(employee="M"), row(employee="M")],
            [row(employee="M"), row(employee="M"), row(employee="PAID")],
        ])
        self.start(patch.dict("sys.modules", {controller.__name__: controller}))
        self.start(patch.object(mixed, "assignments", return_value={
            "B": row(payroll_frequency="Bimonthly"), "M": self.period(), "PAID": self.period()}))
        self.start(patch.object(mixed, "overlaps", side_effect=lambda e, emp, p: [row()] if emp == "PAID" else []))
        result = mixed.employee_list(self.entry, limit=1, offset=1)
        self.assertEqual([r.employee for r in result], ["M"])
        self.assertEqual(controller.get_filtered_employees.call_args_list[1].args[1].start_date, date(2026, 8, 1))
        self.assertFalse(controller.get_filtered_employees.call_args.kwargs["ignore_match_conditions"])

    def test_monthly_slip_validation_remains_strict_after_setting_disabled(self):
        monthly = ModuleType("powerpro.controllers.salary_slip.monthly")
        monthly.lock_employee = Mock()
        self.start(patch.dict("sys.modules", {monthly.__name__: monthly}))
        self.settings.include_monthly_in_second_quincena = 0
        slip = self.slip(new=False)
        slip.payroll_frequency = "Monthly"
        slip.start_date = "2026-08-01"
        overlap = self.start(patch.object(mixed, "overlaps", return_value=[row(name="OTHER")]))
        with self.assertRaises(ValueError):
            mixed.validate_slip(slip)
        monthly.lock_employee.assert_called_once()
        overlap.assert_called_once()

    def test_monthly_slip_cannot_keep_second_half_dates(self):
        monthly = ModuleType("powerpro.controllers.salary_slip.monthly")
        monthly.lock_employee = Mock()
        self.start(patch.dict("sys.modules", {monthly.__name__: monthly}))
        slip = self.slip(new=False)
        slip.payroll_frequency = "Monthly"
        with self.assertRaises(ValueError):
            mixed.validate_slip(slip)

    def worker(self, existing=None):
        upstream = ModuleType("hrms.payroll.doctype.payroll_entry.payroll_entry")
        upstream.log_payroll_failure = Mock()
        monthly = ModuleType("powerpro.controllers.salary_slip.monthly")
        monthly.lock_employee = Mock()
        self.start(patch.dict("sys.modules", {upstream.__name__: upstream, monthly.__name__: monthly}))
        self.entry.employees = [row(employee="M")]
        self.entry.check_permission = Mock()
        self.entry.db_set = Mock()
        self.start(patch.object(mixed, "require_assignment", return_value=self.period()))
        self.start(patch.object(mixed, "overlaps", return_value=existing or []))
        inserted = Mock()
        def get_doc(value, *args):
            return self.entry if value == "Payroll Entry" else inserted
        self.start(patch.object(mixed.frappe, "get_doc", side_effect=get_doc))
        rollback = self.start(patch.object(mixed.frappe.db, "rollback"))
        commit = self.start(patch.object(mixed.frappe.db, "commit"))
        self.start(patch.object(mixed.frappe, "publish_realtime"))
        return upstream, inserted, rollback, commit

    def test_worker_creates_full_month_and_completes_once(self):
        upstream, inserted, rollback, commit = self.worker()
        args = dict(self.entry, payroll_entry=self.entry.name)
        mixed.create_slips(["M"], args)
        inserted.insert.assert_called_once()
        values = mixed.frappe.get_doc.call_args.args[0]
        self.assertEqual(values["payroll_frequency"], "Monthly")
        self.assertEqual(values["start_date"], date(2026, 8, 1))
        rollback.assert_not_called()
        commit.assert_called_once()
        upstream.log_payroll_failure.assert_not_called()

    def test_worker_retry_reuses_same_slip(self):
        existing = row(payroll_entry="PAY-1", payroll_frequency="Monthly", salary_structure="Monthly Structure",
                       start_date="2026-08-01", end_date="2026-08-31")
        upstream, inserted, rollback, commit = self.worker([existing])
        mixed.create_slips(["M"], dict(self.entry, payroll_entry=self.entry.name))
        inserted.insert.assert_not_called()
        rollback.assert_not_called()
        self.entry.db_set.assert_called_once()

    def test_worker_conflict_rolls_back_and_reports_failure(self):
        upstream, inserted, rollback, commit = self.worker([row(payroll_entry="OTHER")])
        mixed.create_slips(["M"], dict(self.entry, payroll_entry=self.entry.name))
        inserted.insert.assert_not_called()
        rollback.assert_called_once()
        upstream.log_payroll_failure.assert_called_once()
        self.entry.db_set.assert_not_called()

    def test_worker_rejects_stale_queue_arguments(self):
        upstream, inserted, rollback, commit = self.worker()
        args = dict(self.entry, payroll_entry=self.entry.name, start_date="2026-07-16")
        mixed.create_slips(["M"], args)
        inserted.insert.assert_not_called()
        rollback.assert_called_once()
        upstream.log_payroll_failure.assert_called_once()

    def test_cancelled_entry_cannot_run_queued_job(self):
        upstream, inserted, rollback, commit = self.worker()
        self.entry.docstatus = 2
        mixed.create_slips(["M"], dict(self.entry, payroll_entry=self.entry.name))
        inserted.insert.assert_not_called()
        rollback.assert_not_called()
        commit.assert_not_called()
        upstream.log_payroll_failure.assert_not_called()
        self.entry.db_set.assert_not_called()


class PayrollControllerBridgeTest(TestCase):
    """Load the actual PowerPro subclass with a recording HRMS parent."""
    def setUp(self):
        class Parent:
            def get(self, name):
                return getattr(self, name, None)

            def get_sal_slip_list(self, ss_status, as_dict=False):
                return self.start_date, self.end_date, self.name, ss_status, as_dict

            def get_salary_slip_details(self, for_withheld_salaries=False):
                return self.start_date, self.end_date, self.name, for_withheld_salaries

            def create_salary_slips(self):
                return "legacy-generation"

            def validate_existing_salary_slips(self):
                return "legacy-validation"

        upstream = ModuleType("hrms.payroll.doctype.payroll_entry.payroll_entry")
        upstream.PayrollEntry = Parent
        package = ModuleType("hrms.payroll.doctype.payroll_entry")
        package.payroll_entry = upstream
        helper = ModuleType("powerpro.controllers.salary_slip.helper")
        helper.LEGACY_EMPLOYER_COMPONENTS = ()
        reportview = ModuleType("frappe.desk.reportview")
        reportview.get_match_cond = Mock()
        patches = patch.dict("sys.modules", {module.__name__: module for module in (upstream, package, helper, reportview)})
        patches.start()
        self.addCleanup(patches.stop)
        spec = importlib.util.spec_from_file_location("_mixed_payroll_controller_test", Path(__file__).with_name("payroll_entry.py"))
        self.controller = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.controller)
        self.entry = self.controller.PayrollEntry()
        self.entry.name = "PAY-1"
        self.entry.docstatus = 1
        self.entry.start_date = "2026-08-16"
        self.entry.end_date = "2026-08-31"
        self.entry.payroll_frequency = "Bimonthly"
        self.entry.salary_slip_based_on_timesheet = 0

    def test_submission_and_bank_queries_include_monthly_period_after_disabling(self):
        with patch.object(mixed.frappe.db, "exists", return_value=True):
            self.assertEqual(self.entry.get_sal_slip_list(0, True),
                             (date(2026, 8, 1), "2026-08-31", "PAY-1", 0, True))
            self.assertEqual(self.entry.get_salary_slip_details(True),
                             (date(2026, 8, 1), "2026-08-31", "PAY-1", True))
        self.assertEqual(self.entry.start_date, "2026-08-16")

    def test_disabled_generation_and_validation_delegate_to_hrms(self):
        with patch.object(mixed, "enabled", return_value=False):
            self.assertEqual(self.entry.create_salary_slips(), "legacy-generation")
            self.assertEqual(self.entry.validate_existing_salary_slips(), "legacy-validation")

    def test_queue_contains_both_groups_and_waits_for_commit(self):
        self.entry.employees = [row(employee=f"EMP-{i}") for i in range(31)]
        self.entry.check_permission = Mock()
        self.entry.db_set = Mock()
        with patch.object(mixed, "enabled", return_value=True), patch.object(frappe, "enqueue", create=True) as enqueue:
            self.entry.create_salary_slips()
        enqueue.assert_called_once()
        self.assertIs(enqueue.call_args.args[0], mixed.create_slips)
        self.assertEqual(len(enqueue.call_args.kwargs["employees"]), 31)
        self.assertTrue(enqueue.call_args.kwargs["enqueue_after_commit"])
        self.assertEqual(enqueue.call_args.kwargs["args"]["payroll_entry"], "PAY-1")
