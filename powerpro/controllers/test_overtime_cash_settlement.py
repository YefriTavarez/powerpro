import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe

from powerpro.controllers import overtime_cash_settlement as settlement


class OvertimeCashSettlementControllerTest(unittest.TestCase):
	def test_paid_adjustment_uses_live_salary_slip_link_as_cancel_guard(self):
		adjustment = SimpleNamespace(
			name="OT-ADJ-2026-00001",
			get=lambda fieldname: "Created" if fieldname == "settlement_status" else None,
		)
		with (
			patch.object(
				settlement,
				"_get_linked_additional_salaries",
				return_value=["SALADIC-26-08-00001"],
			),
			patch.object(
				settlement,
				"_get_submitted_salary_slips",
				return_value=["Sal Slip/Employee/00001"],
			),
			self.assertRaises(frappe.ValidationError),
		):
			settlement.before_cancel_adjustment(adjustment)

	def test_duplicate_additional_salary_is_blocked_before_creation(self):
		adjustment = SimpleNamespace(
			doctype="Retroactive Overtime Adjustment",
			name="OT-ADJ-2026-00001",
		)
		with (
			patch.object(settlement.frappe.db, "get_value", return_value=adjustment.name),
			patch.object(
				settlement,
				"_get_linked_additional_salaries",
				return_value=["SALADIC-26-08-00001"],
			),
			self.assertRaises(frappe.ValidationError),
		):
			settlement._create_additional_salaries(adjustment, {"lines": []})

	def test_salary_slip_submit_marks_fully_included_adjustment_paid(self):
		salary_slip = SimpleNamespace(
			name="Sal Slip/Employee/00001",
			get=lambda fieldname: [
				SimpleNamespace(additional_salary="SALADIC-26-08-00001")
			]
			if fieldname == "earnings"
			else None,
		)
		links = [
			frappe._dict({
				"name": "SALADIC-26-08-00001",
				"ref_docname": "OT-ADJ-2026-00001",
			})
		]
		with (
			patch.object(settlement.frappe, "get_all", return_value=links),
			patch.object(
				settlement,
				"_get_linked_additional_salaries",
				return_value=["SALADIC-26-08-00001"],
			),
			patch.object(settlement.frappe.db, "set_value") as set_value,
		):
			settlement.sync_adjustments_from_salary_slip(salary_slip, paid=True)

		set_value.assert_called_once_with(
			"Retroactive Overtime Adjustment",
			"OT-ADJ-2026-00001",
			{
				"settlement_status": "Paid",
				"settlement_salary_slip": "Sal Slip/Employee/00001",
			},
		)

	def test_partial_salary_slip_does_not_mark_adjustment_paid(self):
		salary_slip = SimpleNamespace(
			name="Sal Slip/Employee/00001",
			get=lambda _fieldname: [
				SimpleNamespace(additional_salary="SALADIC-26-08-00001")
			],
		)
		links = [
			frappe._dict({
				"name": "SALADIC-26-08-00001",
				"ref_docname": "OT-ADJ-2026-00001",
			})
		]
		with (
			patch.object(settlement.frappe, "get_all", return_value=links),
			patch.object(
				settlement,
				"_get_linked_additional_salaries",
				return_value=[
					"SALADIC-26-08-00001",
					"SALADIC-26-08-00002",
				],
			),
			patch.object(settlement.frappe.db, "set_value") as set_value,
		):
			settlement.sync_adjustments_from_salary_slip(salary_slip, paid=True)

		set_value.assert_not_called()

	def test_salary_slip_cancel_returns_adjustment_to_created(self):
		salary_slip = SimpleNamespace(
			name="Sal Slip/Employee/00001",
			get=lambda _fieldname: [
				SimpleNamespace(additional_salary="SALADIC-26-08-00001")
			],
		)
		links = [
			frappe._dict({
				"name": "SALADIC-26-08-00001",
				"ref_docname": "OT-ADJ-2026-00001",
			})
		]
		with (
			patch.object(settlement.frappe, "get_all", return_value=links),
			patch.object(
				settlement,
				"_get_linked_additional_salaries",
				return_value=["SALADIC-26-08-00001"],
			),
			patch.object(settlement.frappe.db, "set_value") as set_value,
		):
			settlement.sync_adjustments_from_salary_slip(salary_slip, paid=False)

		set_value.assert_called_once_with(
			"Retroactive Overtime Adjustment",
			"OT-ADJ-2026-00001",
			{
				"settlement_status": "Created",
				"settlement_salary_slip": None,
			},
		)

	def test_cancelling_unpaid_adjustment_cancels_linked_inputs(self):
		adjustment = SimpleNamespace(
			doctype="Retroactive Overtime Adjustment",
			name="OT-ADJ-2026-00001",
			get=lambda fieldname: "Created" if fieldname == "settlement_status" else None,
		)
		additional_salary = MagicMock()
		with (
			patch.object(
				settlement,
				"_get_linked_additional_salaries",
				return_value=["SALADIC-26-08-00001"],
			),
			patch.object(
				settlement.frappe, "get_doc", return_value=additional_salary
			),
			patch.object(settlement.frappe.db, "set_value") as set_value,
		):
			settlement.cancel_cash_settlement(adjustment)

		additional_salary.cancel.assert_called_once_with()
		set_value.assert_called_once_with(
			"Retroactive Overtime Adjustment",
			"OT-ADJ-2026-00001",
			{
				"status": "Cancelled",
				"settlement_status": "Cancelled",
				"settlement_salary_slip": None,
			},
		)


if __name__ == "__main__":
	unittest.main()
