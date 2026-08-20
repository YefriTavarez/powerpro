import unittest
from types import SimpleNamespace

from powerpro.power_pro.doctype.overtime_authorization.overtime_authorization import (
	apply_employee_approver_snapshot,
	apply_requester_snapshot,
	is_assigned_approver,
)


class OvertimeAuthorizationSecurityTest(unittest.TestCase):
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
