import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


MODULE_NAME = "powerpro_overtime_cash_settlement_rules"
SPEC = spec_from_file_location(
	MODULE_NAME,
	Path(__file__).with_name("overtime_cash_settlement.py"),
)
settlement = module_from_spec(SPEC)
sys.modules[MODULE_NAME] = settlement
SPEC.loader.exec_module(settlement)

calculate_cash_settlement = settlement.calculate_cash_settlement


class OvertimeCashSettlementTest(unittest.TestCase):
	def test_regular_35_percent_amount_matches_salary_component_formula(self):
		result = calculate_cash_settlement(
			hourly_rate=136.38,
			regular_35_hours=10,
			regular_overtime_percent=35,
		)

		self.assertEqual(result["total_amount"], 1841.13)
		self.assertEqual(result["lines"][0]["component"], "Horas Extras 35%")

	def test_100_percent_combines_regular_and_legal_holiday_once(self):
		result = calculate_cash_settlement(
			hourly_rate=100,
			regular_100_hours=2,
			holiday_100_hours=3,
			night_hours=2,
		)

		self.assertEqual(
			result["lines"],
			[
				{
					"component": "Horas Extras 100%",
					"hours": 5.0,
					"hourly_rate": 100.0,
					"premium_percent": 100.0,
					"multiplier": 2.0,
					"amount": 1000.0,
				},
				{
					"component": "Horas Nocturnas",
					"hours": 2.0,
					"hourly_rate": 100.0,
					"premium_percent": 15.0,
					"multiplier": 0.15,
					"amount": 30.0,
				},
			],
		)
		self.assertEqual(result["total_amount"], 1030.0)

	def test_weekly_rest_remains_outside_automatic_cash_settlement(self):
		result = calculate_cash_settlement(
			hourly_rate=100,
			weekly_rest_hours=4,
		)

		self.assertEqual(result["lines"], [])
		self.assertEqual(result["total_amount"], 0)
		self.assertEqual(result["unsettled_weekly_rest_hours"], 4)

	def test_holiday_and_night_premiums_share_the_normal_base(self):
		for covered, additional in [(0, 215), (1, 115), (.5, 165)]:
			with self.subTest(covered=covered):
				r = calculate_cash_settlement(hourly_rate=100, holiday_100_hours=1,
					night_hours=1, holiday_base_covered_hours=covered)
				self.assertEqual(r['total_amount'], additional)
				self.assertEqual(r['total_amount'] + r['holiday_base_already_in_salary'], 215)

	def test_covered_holiday_base_does_not_remove_extraordinary_hour_base(self):
		r = calculate_cash_settlement(hourly_rate=100, regular_100_hours=1,
			holiday_100_hours=1, holiday_base_covered_hours=1, night_hours=2)
		self.assertEqual(r['total_amount'], 330)
		self.assertEqual([x['multiplier'] for x in r['lines']], [2, 1, .15])

	def test_invalid_covered_holiday_hours_are_rejected(self):
		for covered in [-1, 2, float('nan'), float('inf')]:
			with self.subTest(covered=covered), self.assertRaises(ValueError):
				calculate_cash_settlement(hourly_rate=100, holiday_100_hours=1,
					holiday_base_covered_hours=covered)

	def test_zero_hour_lines_are_not_created(self):
		result = calculate_cash_settlement(hourly_rate=100)

		self.assertEqual(result["lines"], [])
		self.assertEqual(result["total_amount"], 0)

	def test_non_positive_hourly_rate_is_rejected(self):
		with self.assertRaises(ValueError):
			calculate_cash_settlement(hourly_rate=0, regular_35_hours=1)


if __name__ == "__main__":
	unittest.main()
