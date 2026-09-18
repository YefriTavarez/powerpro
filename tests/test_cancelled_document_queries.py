"""Exercise generated visibility SQL without a Frappe bench or business writes."""
import ast
import importlib.util
from pathlib import Path
import sqlite3
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
frappe = ModuleType("frappe")
frappe.get_attr = Mock()
spec = importlib.util.spec_from_file_location("cancelled_document_queries", ROOT / "powerpro/utils/cancelled_documents.py")
queries = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {"frappe": frappe}):
    spec.loader.exec_module(queries)

EXPECTED = {
    "Additional Salary", "Asset Maintenance Log", "Attendance", "Delivery Note",
    "Income Tax Slab", "Journal Entry", "Leave Allocation", "Leave Application",
    "Overtime Settlement Election", "Payment Entry", "Payment Ledger Entry",
    "Payroll Bank Batch", "Purchase Invoice", "Quotation",
    "Retroactive Overtime Adjustment", "Salary Slip", "Salary Structure Assignment",
    "Sales Invoice", "Supplier Retainer Batch",
}


class CancelledDocumentQueriesTest(unittest.TestCase):
    def setUp(self):
        frappe.get_attr.reset_mock()
        frappe.get_attr.return_value = Mock(return_value="")
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        for doctype in EXPECTED:
            self.db.execute(f"CREATE TABLE `tab{doctype}` (name TEXT, docstatus INTEGER, allowed INTEGER)")
            self.db.executemany(f"INSERT INTO `tab{doctype}` VALUES (?,?,?)", [
                ("draft", 0, 1), ("submitted", 1, 2), ("cancelled", 2, 1),
                ("other-cancelled", 2, 2), ("restricted-draft", 0, 0),
            ])

    def rows(self, doctype, condition):
        return self.db.execute(f"SELECT name FROM `tab{doctype}` WHERE {condition} ORDER BY name").fetchall()

    def test_registered_scope_is_exact_and_excludes_agreements(self):
        self.assertEqual(queries.FILTERED_DOCTYPES, EXPECTED)
        tree = ast.parse((ROOT / "powerpro/hooks.py").read_text())
        hooks = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "permission_query_conditions" for t in n.targets))
        self.assertEqual({dt for dt, method in hooks.items()
            if method == "powerpro.utils.cancelled_documents.query_conditions"}, EXPECTED)
        self.assertNotIn("Supplier Retainer Agreement", hooks)
        self.assertEqual(hooks["Sales Order"], "powerpro.utils.query.sales_order_query_conditions")
        self.assertEqual(hooks["Customer"], "powerpro.utils.query.customer_query_conditions")

    def test_drafts_and_submitted_remain_for_every_role_including_administrator(self):
        for doctype in EXPECTED:
            for user in (None, "Administrator", "accounts@example.invalid", "employee@example.invalid"):
                with self.subTest(doctype=doctype, user=user):
                    condition = queries.query_conditions(user, doctype)
                    self.assertEqual(self.rows(doctype, condition), [("draft",), ("restricted-draft",), ("submitted",)])
                    self.assertEqual(self.rows(doctype, f"({condition}) AND docstatus=2"), [])

    def test_existing_or_restrictions_are_grouped_and_user_is_forwarded(self):
        for doctype, method in queries.EXISTING_CONDITIONS.items():
            with self.subTest(doctype=doctype):
                previous = Mock(return_value="allowed=1 OR allowed=2")
                frappe.get_attr.return_value = previous
                condition = queries.query_conditions("reviewer@example.invalid", doctype)
                self.assertEqual(self.rows(doctype, condition), [("draft",), ("submitted",)])
                frappe.get_attr.assert_called_with(method)
                previous.assert_called_once_with("reviewer@example.invalid")

    def test_empty_existing_conditions_do_not_exempt_administrator(self):
        for empty in (None, ""):
            frappe.get_attr.return_value = Mock(return_value=empty)
            condition = queries.query_conditions("Administrator", "Asset Maintenance Log")
            self.assertEqual(self.rows("Asset Maintenance Log", condition), [("draft",), ("restricted-draft",), ("submitted",)])

    def test_agreements_other_doctypes_and_unsafe_identifiers_are_untouched(self):
        for doctype in (None, "Supplier Retainer Agreement", "Sales Order", "Employee", "Salary Slip` OR 1=1 --"):
            self.assertEqual(queries.query_conditions("Administrator", doctype), "")
        frappe.get_attr.assert_not_called()

    def test_legacy_query_failure_is_not_silently_bypassed(self):
        frappe.get_attr.return_value = Mock(side_effect=RuntimeError("settings unavailable"))
        with self.assertRaisesRegex(RuntimeError, "settings unavailable"):
            queries.query_conditions("Administrator", "Quotation")


if __name__ == "__main__":
    unittest.main()
