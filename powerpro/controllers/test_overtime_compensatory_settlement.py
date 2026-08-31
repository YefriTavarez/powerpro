import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe

from powerpro.controllers import overtime_compensatory_settlement as settlement


class OvertimeCompensatorySettlementControllerTest(unittest.TestCase):
	def test_standard_compensatory_request_cannot_use_reserved_overtime_type(self):
		request = frappe._dict({
			"employee": "HR-EMP-0001",
			"leave_type": "Overtime Compensatory",
		})
		settings = frappe._dict({
			"enable_overtime_compensatory_settlement": 1,
			"overtime_compensatory_leave_type": "Overtime Compensatory",
		})
		with (
			patch.object(settlement.frappe, "get_single", return_value=settings),
			patch.object(settlement.frappe.db, "exists", return_value=False),
			self.assertRaises(frappe.ValidationError),
		):
			settlement.protect_overtime_leave_type_from_standard_request(
				request, "before_submit"
			)

	def test_managed_allocation_rejects_manual_changes(self):
		allocation = MagicMock()
		allocation.meta.has_field.return_value = True
		allocation.get.side_effect = lambda fieldname: (
			1 if fieldname == "powerpro_overtime_managed" else None
		)
		allocation.flags = SimpleNamespace(get=lambda _fieldname: False)
		with self.assertRaises(frappe.ValidationError):
			settlement.protect_managed_leave_allocation(allocation)

	def test_team_preview_accumulates_hours_before_writing(self):
		settings = frappe._dict({
			"overtime_compensatory_leave_type": "Compensatory",
			"overtime_hours_per_leave_day": 8,
			"overtime_leave_increment": 0.5,
		})
		leave_period = frappe._dict({
			"name": "HR-LP-2026",
			"from_date": "2026-01-01",
			"to_date": "2026-12-31",
		})
		first = frappe._dict({
			"name": "OT-AUTH-0001",
			"employee": "HR-EMP-0001",
			"company": "IGC",
			"employee_name": "Employee One",
			"work_date": "2026-08-16",
			"verified_hours": 3,
		})
		second = frappe._dict({**first, "name": "OT-AUTH-0002"})
		bank_state = {}
		with (
			patch.object(settlement, "_validate_configuration"),
			patch.object(settlement, "_get_leave_period", return_value=leave_period),
			patch.object(
				settlement,
				"_get_bank_totals",
				return_value={"active_hours": 0, "effective_days": 0},
			),
			patch.object(settlement, "_find_managed_allocation", return_value=None),
		):
			first_preview = settlement.build_compensatory_preview(
				first, settings=settings, bank_state=bank_state
			)
			second_preview = settlement.build_compensatory_preview(
				second, settings=settings, bank_state=bank_state
			)

		self.assertEqual(first_preview["days_to_credit"], 0)
		self.assertEqual(second_preview["days_to_credit"], 0.5)
		self.assertEqual(second_preview["residual_hours"], 2)

	def test_bank_totals_keep_cancelled_credit_and_its_reversal_auditable(self):
		rows = [
			frappe._dict({
				"docstatus": 2,
				"banked_hours": 3,
				"credited_days": 0,
				"reversed_days": 0.5,
			}),
			frappe._dict({
				"docstatus": 1,
				"banked_hours": 3,
				"credited_days": 0.5,
				"reversed_days": 0,
			}),
		]
		with patch.object(settlement.frappe, "get_all", return_value=rows):
			result = settlement._get_bank_totals(
				"HR-EMP-0001", "IGC", "Compensatory", "HR-LP-2026"
			)

		self.assertEqual(result["active_hours"], 3)
		self.assertEqual(result["effective_days"], 0)

	def test_manual_overlapping_allocation_is_never_adopted(self):
		rows = [
			frappe._dict({
				"name": "HR-LAL-2026-00001",
				"from_date": "2026-01-01",
				"to_date": "2026-12-31",
				"powerpro_overtime_managed": 0,
				"powerpro_overtime_leave_period": None,
			})
		]
		leave_period = frappe._dict({
			"name": "HR-LP-2026",
			"from_date": "2026-01-01",
			"to_date": "2026-12-31",
		})
		with (
			patch.object(settlement.frappe, "get_all", return_value=rows),
			self.assertRaises(frappe.ValidationError),
		):
			settlement._find_managed_allocation(
				"HR-EMP-0001",
				"Compensatory",
				leave_period,
			)

	def test_existing_managed_allocation_is_reused(self):
		rows = [
			frappe._dict({
				"name": "HR-LAL-2026-00002",
				"from_date": "2026-01-01",
				"to_date": "2026-12-31",
				"powerpro_overtime_managed": 1,
				"powerpro_overtime_leave_period": "HR-LP-2026",
			})
		]
		leave_period = frappe._dict({
			"name": "HR-LP-2026",
			"from_date": "2026-01-01",
			"to_date": "2026-12-31",
		})
		with patch.object(settlement.frappe, "get_all", return_value=rows):
			result = settlement._find_managed_allocation(
				"HR-EMP-0001",
				"Compensatory",
				leave_period,
			)

		self.assertEqual(result.name, "HR-LAL-2026-00002")


if __name__ == "__main__":
	unittest.main()
