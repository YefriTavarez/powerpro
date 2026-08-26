import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


MODULE_NAME = "powerpro_retroactive_overtime_rules"
RULES_PATH = Path(__file__).parents[3] / "payroll_rules" / "retroactive_overtime.py"
SPEC = spec_from_file_location(MODULE_NAME, RULES_PATH)
retroactive = module_from_spec(SPEC)
sys.modules[MODULE_NAME] = retroactive
SPEC.loader.exec_module(retroactive)

is_adjustment_date_allowed = retroactive.is_adjustment_date_allowed
is_completed_historical_window = retroactive.is_completed_historical_window
is_review_window_on_work_date = retroactive.is_review_window_on_work_date
is_submission_deadline_open = retroactive.is_submission_deadline_open
select_last_valid_out_checkin = retroactive.select_last_valid_out_checkin


class RetroactiveOvertimeAdjustmentPolicyTest(unittest.TestCase):
	def test_submission_deadline_is_inclusive(self):
		self.assertTrue(is_submission_deadline_open("2026-09-15", "2026-09-15"))
		self.assertFalse(is_submission_deadline_open("2026-09-15", "2026-09-16"))
		self.assertFalse(is_submission_deadline_open(None, "2026-09-15"))

	def test_allowed_historical_period_is_closed_and_inclusive(self):
		self.assertTrue(
			is_adjustment_date_allowed("2026-07-01", "2026-07-01", "2026-08-31")
		)
		self.assertTrue(
			is_adjustment_date_allowed("2026-08-31", "2026-07-01", "2026-08-31")
		)
		self.assertFalse(
			is_adjustment_date_allowed("2026-06-30", "2026-07-01", "2026-08-31")
		)

	def test_only_completed_work_can_be_adjusted(self):
		self.assertTrue(
			is_completed_historical_window(
				"2026-08-19 20:00:00", "2026-08-20 09:00:00"
			)
		)
		self.assertFalse(
			is_completed_historical_window(
				"2026-08-20 20:00:00", "2026-08-20 09:00:00"
			)
		)

	def test_day_shift_window_cannot_span_multiple_dates(self):
		self.assertTrue(
			is_review_window_on_work_date(
				"2026-08-10",
				"2026-08-10 16:00:00",
				"2026-08-10 20:40:11",
			)
		)
		self.assertFalse(
			is_review_window_on_work_date(
				"2026-08-10",
				"2026-08-10 10:47:03",
				"2026-08-15 10:47:03",
			)
		)

	def test_overnight_shift_may_end_only_on_following_date(self):
		self.assertTrue(
			is_review_window_on_work_date(
				"2026-08-10",
				"2026-08-10 22:00:00",
				"2026-08-11 06:30:00",
				allow_overnight=True,
			)
		)
		self.assertFalse(
			is_review_window_on_work_date(
				"2026-08-10",
				"2026-08-10 22:00:00",
				"2026-08-12 06:30:00",
				allow_overnight=True,
			)
		)

	def test_last_out_after_day_shift_is_selected_on_same_work_date(self):
		checkins = [
			{"name": "BREAK", "time": "2026-08-10 12:00:00", "log_type": "OUT"},
			{"name": "FIRST-OUT", "time": "2026-08-10 18:00:00", "log_type": "OUT"},
			{"name": "LAST-OUT", "time": "2026-08-10 20:40:11", "log_type": "OUT"},
			{"name": "NEXT-DAY", "time": "2026-08-11 05:00:00", "log_type": "OUT"},
		]

		selected = select_last_valid_out_checkin(
			checkins,
			"2026-08-10 06:00:00",
			"2026-08-10 16:00:00",
			shift_type="Diurna Anticipada",
		)

		self.assertEqual(selected["name"], "LAST-OUT")

	def test_overnight_shift_accepts_following_day_out_before_next_shift(self):
		checkins = [
			{"name": "SHIFT-END", "time": "2026-08-11 06:00:00", "log_type": "OUT"},
			{"name": "LATE-OUT", "time": "2026-08-11 07:30:00", "log_type": "OUT"},
			{"name": "NEXT-SHIFT", "time": "2026-08-11 22:30:00", "log_type": "OUT"},
		]

		selected = select_last_valid_out_checkin(
			checkins,
			"2026-08-10 22:00:00",
			"2026-08-11 06:00:00",
		)

		self.assertEqual(selected["name"], "LATE-OUT")

	def test_out_from_another_shift_is_not_selected(self):
		checkins = [
			{
				"name": "OTHER-SHIFT",
				"time": "2026-08-10 20:00:00",
				"log_type": "OUT",
				"shift": "Nocturna",
			},
			{
				"name": "MATCHING-SHIFT",
				"time": "2026-08-10 19:00:00",
				"log_type": "OUT",
				"shift": "Diurna Anticipada",
			},
		]

		selected = select_last_valid_out_checkin(
			checkins,
			"2026-08-10 06:00:00",
			"2026-08-10 16:00:00",
			shift_type="Diurna Anticipada",
		)

		self.assertEqual(selected["name"], "MATCHING-SHIFT")

	def test_missing_out_does_not_invent_a_reviewed_end(self):
		selected = select_last_valid_out_checkin(
			[
				{"time": "2026-08-10 18:00:00", "log_type": "IN"},
				{
					"time": "2026-08-10 18:30:00",
					"log_type": "OUT",
					"accion": "Inicio Break",
				},
				{"time": "2026-08-10 19:00:00", "accion": "Manual"},
			],
			"2026-08-10 06:00:00",
			"2026-08-10 16:00:00",
		)

		self.assertIsNone(selected)

	def test_legacy_final_shift_action_can_supply_out_when_log_type_is_blank(self):
		selected = select_last_valid_out_checkin(
			[
				{"name": "BREAK", "time": "2026-08-10 17:00:00", "accion": "Inicio Break"},
				{"name": "FINAL", "time": "2026-08-10 19:00:00", "accion": "Fin Jornada"},
			],
			"2026-08-10 06:00:00",
			"2026-08-10 16:00:00",
		)

		self.assertEqual(selected["name"], "FINAL")


if __name__ == "__main__":
	unittest.main()
