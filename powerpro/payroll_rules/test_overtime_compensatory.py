import sys
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


MODULE_NAME = "powerpro_overtime_compensatory_rules"
SPEC = spec_from_file_location(
	MODULE_NAME, Path(__file__).with_name("overtime_compensatory.py")
)
rules = module_from_spec(SPEC)
sys.modules[MODULE_NAME] = rules
SPEC.loader.exec_module(rules)


class OvertimeCompensatoryRulesTest(unittest.TestCase):
	def test_retains_hours_below_half_day_increment(self):
		result = rules.calculate_compensatory_credit(
			active_hours_before=0,
			current_hours=3,
			effective_days_before=0,
			hours_per_day=8,
			leave_increment=0.5,
		)
		self.assertEqual(result["days_to_credit"], 0)
		self.assertEqual(result["residual_hours"], 3)

	def test_combines_multiple_authorizations_into_one_increment(self):
		result = rules.calculate_compensatory_credit(
			active_hours_before=3,
			current_hours=3,
			effective_days_before=0,
			hours_per_day=8,
			leave_increment=0.5,
		)
		self.assertEqual(result["days_to_credit"], 0.5)
		self.assertEqual(result["residual_hours"], 2)

	def test_credits_only_increment_not_total_bank_again(self):
		result = rules.calculate_compensatory_credit(
			active_hours_before=6,
			current_hours=2,
			effective_days_before=0.5,
			hours_per_day=8,
			leave_increment=0.5,
		)
		self.assertEqual(result["target_days"], 1)
		self.assertEqual(result["days_to_credit"], 0.5)
		self.assertEqual(result["residual_hours"], 0)

	def test_reversal_rebalances_days_even_when_cancelled_credit_added_no_days(self):
		result = rules.calculate_compensatory_reversal(
			active_hours_before=6,
			hours_to_reverse=3,
			effective_days_before=0.5,
			hours_per_day=8,
			leave_increment=0.5,
		)
		self.assertEqual(result["days_to_reverse"], 0.5)
		self.assertEqual(result["residual_hours_after"], 3)

	def test_rejects_reversing_hours_outside_active_bank(self):
		with self.assertRaises(ValueError):
			rules.calculate_compensatory_reversal(
				active_hours_before=3,
				hours_to_reverse=4,
				effective_days_before=0,
				hours_per_day=8,
				leave_increment=0.5,
			)


if __name__ == "__main__":
	unittest.main()
