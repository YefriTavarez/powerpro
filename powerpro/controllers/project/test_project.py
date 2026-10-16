# Copyright (c) 2026, Yefri Tavarez and Contributors
# For license information, please see license.txt

"""Regression checks for ERPNext progress methods used by PowerPro Project."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import frappe
from erpnext.projects.doctype.project import project as erpnext_project

from powerpro.controllers.project.project import Project


class TestProjectProgress(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
