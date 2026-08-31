import unittest
from unittest.mock import patch

import frappe

from powerpro.controllers import overtime_settlement as settlement


def authorization(**overrides):
	values = {
		"doctype": "Overtime Authorization",
		"name": "OT-AUTH-2026-00001",
		"docstatus": 1,
		"status": "Approved",
		"settlement_status": "Pending",
		"reconciliation_status": "Completed",
		"reconciled_on": "2026-08-17 08:00:00",
		"verified_hours": 4,
		"planned_settlement": "Cash",
		"regular_35_hours": 4,
		"regular_100_hours": 0,
		"holiday_100_hours": 0,
		"weekly_rest_hours": 0,
		"night_hours": 0,
	}
	values.update(overrides)
	return frappe._dict(values)


class OvertimeSettlementControllerTest(unittest.TestCase):
	def test_completed_reconciled_cash_authorization_is_ready(self):
		settlement._validate_ready(authorization())

	def test_scheduled_authorization_cannot_settle(self):
		with self.assertRaises(frappe.ValidationError):
			settlement._validate_ready(
				authorization(reconciliation_status="Scheduled", reconciled_on=None)
			)

	def test_duplicate_settlement_is_blocked(self):
		with self.assertRaises(frappe.ValidationError):
			settlement._validate_ready(authorization(settlement_status="Created"))

	def test_cash_requires_frozen_payroll_classification(self):
		with self.assertRaises(frappe.ValidationError):
			settlement._validate_ready(authorization(regular_35_hours=0))

	def test_compensatory_rest_uses_verified_hours_without_cash_categories(self):
		settlement._validate_ready(
			authorization(planned_settlement="Compensatory Rest", regular_35_hours=0)
		)

	def test_compensatory_cancel_reverses_credit_and_marks_source_cancelled(self):
		doc = authorization(
			settlement_status="Credited",
			settlement_method="Compensatory Rest",
		)
		with (
			patch.object(
				settlement,
				"reverse_compensatory_credit",
				return_value={"days_to_reverse": 0.5},
			) as reverse,
			patch.object(settlement.frappe.db, "set_value") as set_value,
		):
			result = settlement.cancel_authorization_settlement(doc)

		reverse.assert_called_once_with(doc)
		set_value.assert_called_once_with(
			"Overtime Authorization",
			"OT-AUTH-2026-00001",
			{"status": "Cancelled", "settlement_status": "Cancelled"},
		)
		self.assertEqual(result["days_to_reverse"], 0.5)


if __name__ == "__main__":
	unittest.main()

