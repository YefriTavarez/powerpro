# Copyright (c) 2026, Yefri Tavarez and Contributors
# For license information, please see license.txt

"""Regression checks for ERPNext progress and costing used by PowerPro Project."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

import frappe
from erpnext.projects.doctype.project import project as erpnext_project

from powerpro.controllers.project.project import Project
from powerpro.controllers.task.task import Task


class ProjectTestCase(unittest.TestCase):
    def setUp(self):
        # flt(..., precision) lazily reads System Settings. Keep that lookup
        # outside the task SQL/cached-document mocks, even with a cold cache.
        system_settings = frappe.get_system_settings

        def get_setting(key):
            if key == "rounding_method":
                return "Banker's Rounding"
            return system_settings(key)

        settings = patch.object(frappe, "get_system_settings", side_effect=get_setting)
        settings.start()
        self.addCleanup(settings.stop)


class TestProjectProgress(ProjectTestCase):
    def make_project(self, method="Task Completion", status="Open", previous="Open"):
        # The progress methods only need document fields; no persisted fixture.
        doc = Project.__new__(Project)
        doc.name = "TEST-PROJECT-PROGRESS"
        doc.status = status
        doc.percent_complete = 0
        doc.percent_complete_method = method
        doc.project_template = "TEST-TEMPLATE"
        doc.get_doc_before_save = Mock(return_value=SimpleNamespace(status=previous))
        doc.db_update = Mock()
        doc.notify_update = Mock()
        return doc

    def test_project_validation_recalculates_incomplete_tasks(self):
        doc = self.make_project()
        with patch.object(frappe.db, "count", return_value=4), patch.object(
            frappe.db, "sql", return_value=[(1,)]
        ):
            doc.validate()
        self.assertEqual(doc.percent_complete, 25)
        self.assertEqual(doc.status, "Open")

    def test_task_update_recalculates_and_persists_project(self):
        doc = self.make_project()
        with patch.object(frappe.db, "count", return_value=2), patch.object(
            frappe.db, "sql", return_value=[(2,)]
        ), patch.object(erpnext_project.Project, "update_costing") as costing:
            doc.update_project()
        self.assertEqual(doc.percent_complete, 100)
        self.assertEqual(doc.status, "Completed")
        costing.assert_called_once_with(doc)
        doc.db_update.assert_called_once_with()
        doc.notify_update.assert_called_once_with()

    @unittest.skipUnless(
        hasattr(erpnext_project.Project, "validate_completed_status"),
        "ERPNext version predates native completion validation",
    )
    def test_premature_manual_completion_remains_rejected(self):
        doc = self.make_project(status="Completed")
        with patch.object(frappe, "get_all", return_value=[{"name": "TASK-1"}]), patch.object(
            frappe.db, "count", return_value=2
        ), patch.object(frappe.db, "sql", return_value=[(1,)]):
            with self.assertRaises(frappe.ValidationError):
                doc.validate()

    def test_manual_progress_is_preserved(self):
        doc = self.make_project(method="Manual")
        doc.percent_complete = 37
        doc.validate()
        self.assertEqual(doc.percent_complete, 37)
        self.assertEqual(doc.status, "Open")

    def test_cancelled_and_on_hold_statuses_are_preserved(self):
        for status in ("Cancelled", "On hold"):
            with self.subTest(status=status):
                doc = self.make_project(status=status)
                with patch.object(frappe.db, "count", return_value=2), patch.object(
                    frappe.db, "sql", return_value=[(2,)]
                ):
                    doc.validate()
                self.assertEqual(doc.status, status)

    @unittest.skipUnless(
        hasattr(erpnext_project.Project, "get_task_progress"),
        "ERPNext version predates native task progress helper",
    )
    def test_task_progress_and_weight_use_native_calculation(self):
        tasks = [
            SimpleNamespace(status="Open", progress=20, task_weight=1),
            SimpleNamespace(status="Completed", progress=0, task_weight=3),
        ]
        for method, expected in (("Task Progress", 60), ("Task Weight", 80)):
            with self.subTest(method=method):
                doc = self.make_project(method=method)
                with patch.object(frappe.db, "count", return_value=2), patch.object(
                    frappe, "get_all", return_value=tasks
                ):
                    doc.validate()
                self.assertEqual(doc.percent_complete, expected)
                self.assertEqual(doc.status, "Open")


@unittest.skipUnless(
    hasattr(erpnext_project.Project, "get_non_stock_purchase_cost"),
    "ERPNext version predates split purchase costing helpers",
)
class TestProjectPurchaseCosting(ProjectTestCase):
    def make_query(self, results):
        # Keep the native ERPNext costing methods; mock only database results.
        query = MagicMock()
        for method in ("left_join", "on", "select", "where"):
            getattr(query, method).return_value = query
        query.run.side_effect = results
        return query

    def test_purchase_cost_includes_all_capitalised_landed_costs(self):
        for purchase, landed in ((1250.75, 50.25), (None, None), (-125.5, -5.25)):
            with self.subTest(purchase=purchase, landed=landed):
                doc = Project.__new__(Project)
                doc.name = "TEST-PROJECT-COSTING"
                receipt_types = erpnext_project.LANDED_COST_RECEIPT_ITEMS
                query = self.make_query([[(purchase,)]] + [[(landed,)]] * len(receipt_types))
                with patch.object(erpnext_project.qb, "from_", return_value=query):
                    doc.update_purchase_costing()
                self.assertAlmostEqual(
                    doc.total_purchase_cost,
                    (purchase or 0) - (landed or 0) * len(receipt_types),
                )
                self.assertEqual(query.run.call_count, 1 + len(receipt_types))

    def test_task_update_reaches_native_costing_and_persists_project(self):
        doc = Project.__new__(Project)
        doc.name = "TEST-PROJECT-COSTING"
        doc.status = "Open"
        doc.percent_complete = 0
        doc.percent_complete_method = "Task Completion"
        doc.total_consumed_material_cost = 200
        doc.get_doc_before_save = Mock(return_value=SimpleNamespace(status="Open"))
        doc.db_update = Mock()
        doc.notify_update = Mock()
        timesheet = SimpleNamespace(
            start_date=None, end_date=None, costing_amount=100,
            billing_amount=180, time=2,
        )
        receipt_count = len(erpnext_project.LANDED_COST_RECEIPT_ITEMS)
        query = self.make_query(
            [[timesheet], [(1250.75,)]] + [[(50.25,)]] * receipt_count
        )
        task = Task.__new__(Task)
        task.project = doc.name
        task.flags = SimpleNamespace(from_project=False)
        with patch.object(frappe, "get_cached_doc", return_value=doc), patch.object(
            frappe.db, "count", return_value=2
        ), patch.object(
            frappe.db, "sql", side_effect=[[(1,)], [(2000,)], [(1800,)], [(100,)]]
        ), patch.object(erpnext_project.qb, "from_", return_value=query):
            task.update_project()
        purchase_cost = 1250.75 - 50.25 * receipt_count
        self.assertEqual(doc.percent_complete, 50)
        self.assertEqual(doc.status, "Open")
        self.assertEqual(doc.total_purchase_cost, purchase_cost)
        self.assertEqual(doc.total_sales_amount, 2000)
        self.assertEqual(doc.total_billed_amount, 1900)
        self.assertEqual(doc.actual_time, 2)
        self.assertEqual(doc.gross_margin, 1900 - 100 - purchase_cost - 200)
        self.assertAlmostEqual(doc.per_gross_margin, doc.gross_margin / 1900 * 100)
        doc.db_update.assert_called_once_with()
        doc.notify_update.assert_called_once_with()

    def test_database_failure_is_not_silently_converted_to_zero_cost(self):
        doc = Project.__new__(Project)
        doc.name = "TEST-PROJECT-COSTING"
        doc.total_purchase_cost = 123
        query = self.make_query([])
        query.run.side_effect = RuntimeError("cost query failed")
        with patch.object(erpnext_project.qb, "from_", return_value=query):
            with self.assertRaisesRegex(RuntimeError, "cost query failed"):
                doc.update_purchase_costing()
        self.assertEqual(doc.total_purchase_cost, 123)


if __name__ == "__main__":
    unittest.main()
