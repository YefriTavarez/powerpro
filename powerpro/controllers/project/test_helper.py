# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import unittest
from unittest.mock import patch, MagicMock
import powerpro.controllers.project.helper as helper

class TestHelper(unittest.TestCase):
    @patch("powerpro.controllers.project.helper")
    def test_get_users_from_template_as_list(self, mock_frappe):
        doc = MagicMock()
        doc.status = "Template"
        doc.users = [MagicMock(user="user1"), MagicMock(user="user2")]
        mock_frappe.get_doc.return_value = doc

        result = helper.get_users_from_template("TASK-001", as_list=True)
        self.assertEqual(result, ["user1", "user2"])

    @patch("powerpro.controllers.project.helper")
    def test_get_users_from_template_as_docs(self, mock_frappe):
        doc = MagicMock()
        doc.status = "Template"
        doc.users = [MagicMock(), MagicMock()]
        mock_frappe.get_doc.return_value = doc
        mock_frappe.copy_doc.side_effect = lambda x: f"copied_{id(x)}"

        result = helper.get_users_from_template("TASK-001", as_list=False)
        self.assertTrue(all(str(r).startswith("copied_") for r in result))
        self.assertEqual(len(result), 2)

    @patch("powerpro.controllers.project.helper")
    def test_get_users_from_template_not_template(self, mock_frappe):
        doc = MagicMock()
        doc.status = "Open"
        mock_frappe.get_doc.return_value = doc
        mock_frappe.throw.side_effect = Exception("Not a template")

        with self.assertRaises(Exception) as cm:
            helper.get_users_from_template("TASK-001")
        self.assertIn("Not a template", str(cm.exception))

    @patch("powerpro.controllers.project.helper")
    def test_get_depends_on_tasks_from_template_only_names(self, mock_frappe):
        doc = MagicMock()
        doc.status = "Template"
        doc.depends_on = [MagicMock(task="TASK-002"), MagicMock(task="TASK-003")]
        mock_frappe.get_doc.return_value = doc

        result = helper.get_depends_on_tasks_from_template("TASK-001", only_names=True)
        self.assertEqual(result, ["TASK-002", "TASK-003"])

    @patch("powerpro.controllers.project.helper")
    def test_get_depends_on_tasks_from_template_empty(self, mock_frappe):
        doc = MagicMock()
        doc.status = "Template"
        doc.depends_on = []
        mock_frappe.get_doc.return_value = doc

        result = helper.get_depends_on_tasks_from_template("TASK-001")
        self.assertEqual(result, [])

    @patch("powerpro.controllers.project.helper")
    def test_get_depends_on_tasks_from_template_not_template(self, mock_frappe):
        doc = MagicMock()
        doc.status = "Open"
        mock_frappe.get_doc.return_value = doc
        mock_frappe.throw.side_effect = Exception("Not a template")

        with self.assertRaises(Exception) as cm:
            helper.get_depends_on_tasks_from_template("TASK-001")
        self.assertIn("Not a template", str(cm.exception))

    @patch("powerpro.controllers.project.helper")
    def test_get_depends_on_tasks_from_template_with_tasks(self, mock_frappe):
        doc = MagicMock()
        doc.status = "Template"
        doc.depends_on = [MagicMock(task="TEMPLATE-1", idx=1)]
        doc.project = "PROJECT-1"
        doc.name = "TASK-001"
        mock_frappe.get_doc.return_value = doc
        mock_frappe.get_value.return_value = "TASK-REAL-1"
        mock_frappe.new_doc.side_effect = lambda doctype: MagicMock(**{"task": None, "idx": 1, "parent": None, "parenttype": None, "parentfield": None})

        result = helper.get_depends_on_tasks_from_template("TASK-001")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].task, "TASK-REAL-1")

    @patch("powerpro.controllers.project.helper")
    def test_get_depends_on_tasks_from_template_missing_task(self, mock_frappe):
        doc = MagicMock()
        doc.status = "Template"
        doc.depends_on = [MagicMock(task="TEMPLATE-1", idx=1)]
        doc.project = "PROJECT-1"
        doc.name = "TASK-001"
        mock_frappe.get_doc.return_value = doc
        mock_frappe.get_value.return_value = None
        mock_frappe.throw.side_effect = Exception("No such task")

        with self.assertRaises(Exception) as cm:
            helper.get_depends_on_tasks_from_template("TASK-001")
        self.assertIn("No such task", str(cm.exception))

if __name__ == "__main__":
    unittest.main()
