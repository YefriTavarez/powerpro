import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from powerpro.power_pro.doctype.overtime_authorization.overtime_authorization import (
	OvertimeAuthorization,
	apply_employee_approver_snapshot,
	OvertimeAuthorization,
	apply_requester_snapshot,
	is_assigned_approver,
)

from powerpro.power_pro.doctype.retroactive_overtime_adjustment.retroactive_overtime_adjustment import (
	RetroactiveOvertimeAdjustment,
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


class OvertimeWorkCallSourceTest(unittest.TestCase):
	def setUp(self):
		self.get_doc = patch(
			"powerpro.power_pro.doctype.overtime_authorization.overtime_authorization.frappe.get_doc"
		).start()
		self.addCleanup(patch.stopall)
		patch(
			"powerpro.power_pro.doctype.overtime_authorization.overtime_authorization._",
			side_effect=lambda message: message,
		).start()
		patch(
			"powerpro.power_pro.doctype.overtime_authorization.overtime_authorization.frappe.throw",
			side_effect=lambda message, *args, **kwargs: self._reject(message),
		).start()

	@staticmethod
	def _reject(message):
		raise ValueError(message)

	def authorization(self, cls=OvertimeAuthorization, **values):
		# Use the real inherited methods without initializing a site or writing records.
		doc = object.__new__(cls)
		doc.__dict__.update({
			"doctype": "Overtime Authorization",
			"flags": {},
			"employee": "EMP-TEST",
			"work_date": "2026-08-13",
			"authorization_start": "2026-08-13 18:00:00",
			"authorization_end": "2026-08-13 21:00:00",
			"maximum_hours": 3,
			"precision": lambda fieldname: 2,
			**values,
		})
		return doc

	def source(self, **values):
		return SimpleNamespace(**{
			"docstatus": 1,
			"employees": [SimpleNamespace(employee="EMP-TEST")],
			"dates": [SimpleNamespace(
				work_date="2026-08-13", start_time="18:00:00",
				end_time="21:00:00", requested_hours=3,
			)],
			**values,
		})

	def test_retroactive_adjustment_without_work_call_field(self):
		doc = self.authorization(
			RetroactiveOvertimeAdjustment, doctype="Retroactive Overtime Adjustment"
		)
		self.assertFalse(hasattr(doc, "overtime_work_call"))
		doc._validate_work_call_source()
		self.get_doc.assert_not_called()

	def test_standalone_authorization_without_source(self):
		self.authorization(overtime_work_call=None)._validate_work_call_source()
		self.get_doc.assert_not_called()

	def test_new_manually_linked_authorization_is_rejected(self):
		doc = self.authorization(overtime_work_call="CALL-TEST", __islocal=1)
		with self.assertRaisesRegex(ValueError, "cannot be supplied manually"):
			doc._validate_work_call_source()
		self.get_doc.assert_not_called()

	def test_generated_authorization_accepts_matching_submitted_source(self):
		doc = self.authorization(
			overtime_work_call="CALL-TEST", __islocal=1,
			flags={"generated_from_overtime_work_call": True},
		)
		self.get_doc.return_value = self.source()
		doc._validate_work_call_source()
		self.get_doc.assert_called_once_with("Overtime Work Call", "CALL-TEST")

	def test_unsubmitted_source_is_rejected(self):
		self.get_doc.return_value = self.source(docstatus=0)
		with self.assertRaisesRegex(ValueError, "must be submitted"):
			self.authorization(overtime_work_call="CALL-TEST")._validate_work_call_source()

	def test_employee_outside_source_is_rejected(self):
		self.get_doc.return_value = self.source(employees=[])
		with self.assertRaisesRegex(ValueError, "Employee is not included"):
			self.authorization(overtime_work_call="CALL-TEST")._validate_work_call_source()

	def test_date_outside_source_is_rejected(self):
		self.get_doc.return_value = self.source(dates=[])
		with self.assertRaisesRegex(ValueError, "Work Date is not included"):
			self.authorization(overtime_work_call="CALL-TEST")._validate_work_call_source()

	def test_changed_window_is_rejected(self):
		self.get_doc.return_value = self.source()
		doc = self.authorization(
			overtime_work_call="CALL-TEST", authorization_end="2026-08-13 22:00:00"
		)
		with self.assertRaisesRegex(ValueError, "window does not match"):
			doc._validate_work_call_source()


if __name__ == "__main__":
	unittest.main()
