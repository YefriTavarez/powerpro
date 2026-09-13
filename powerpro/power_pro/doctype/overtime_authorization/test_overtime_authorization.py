import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from powerpro.power_pro.doctype.overtime_authorization.overtime_authorization import (
	apply_employee_approver_snapshot,
	OvertimeAuthorization,
	apply_requester_snapshot,
	is_assigned_approver,
)


class OvertimeAuthorizationSecurityTest(unittest.TestCase):
	def test_inherited_validation_allows_documents_without_work_call_field(self):
		doc = SimpleNamespace(get=lambda field: None)
		with patch("frappe.get_doc") as load:
			OvertimeAuthorization._validate_work_call_source(doc)
		load.assert_not_called()

	def test_supplied_work_call_still_requires_source_generation(self):
		doc = SimpleNamespace(
			get=lambda field: "CALL-1", overtime_work_call="CALL-1",
			flags={}, is_new=lambda: True,
		)
		with patch("frappe.throw", side_effect=PermissionError), patch("frappe.get_doc") as load:
			with self.assertRaises(PermissionError):
				OvertimeAuthorization._validate_work_call_source(doc)
		load.assert_not_called()

	def test_pending_settlement_method_has_blank_select_option(self):
		doctype_path = Path(__file__).with_name("overtime_authorization.json")
		metadata = json.loads(doctype_path.read_text())
		settlement_method = next(
			field
			for field in metadata["fields"]
			if field.get("fieldname") == "settlement_method"
		)

		self.assertEqual(
			settlement_method["options"].split("\n"),
			["", "Cash", "Compensatory Rest"],
		)

	def test_employee_approver_overwrites_client_supplied_value(self):
		authorization = SimpleNamespace(approver="attacker@example.com")
		employee = SimpleNamespace(overtime_approver="assigned@example.com")

		apply_employee_approver_snapshot(authorization, employee)

		self.assertEqual(authorization.approver, "assigned@example.com")

	def test_only_assigned_approver_can_submit(self):
		self.assertTrue(
			is_assigned_approver("assigned@example.com", "assigned@example.com")
		)
		self.assertFalse(
			is_assigned_approver("assigned@example.com", "Administrator")
		)

	def test_document_owner_overwrites_client_supplied_requester(self):
		authorization = SimpleNamespace(
			owner="requester@example.com",
			requested_by="attacker@example.com",
		)

		apply_requester_snapshot(authorization, "editor@example.com")

		self.assertEqual(authorization.requested_by, "requester@example.com")

	def test_new_document_uses_acting_user_as_requester(self):
		authorization = SimpleNamespace(owner=None, requested_by=None)

		apply_requester_snapshot(authorization, "requester@example.com")

		self.assertEqual(authorization.requested_by, "requester@example.com")


if __name__ == "__main__":
	unittest.main()
