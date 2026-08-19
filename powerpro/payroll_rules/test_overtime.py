import unittest
from datetime import datetime
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


# Load this pure rules module without importing powerpro/__init__.py. The app's
# package initializer intentionally imports Frappe and is unavailable in the
# lightweight unit-test runtime used by CI for calculation-only tests.
MODULE_NAME = "powerpro_overtime_rules"
SPEC = spec_from_file_location(MODULE_NAME, Path(__file__).with_name("overtime.py"))
overtime = module_from_spec(SPEC)
sys.modules[MODULE_NAME] = overtime
SPEC.loader.exec_module(overtime)

HOLIDAY_ON_WEEKLY_REST = overtime.HOLIDAY_ON_WEEKLY_REST
LEGAL_HOLIDAY = overtime.LEGAL_HOLIDAY
REGULAR_DAY = overtime.REGULAR_DAY
WEEKLY_REST = overtime.WEEKLY_REST
classify_workday = overtime.classify_workday
get_shift_window = overtime.get_shift_window
holiday_list_covers = overtime.holiday_list_covers
reconcile_authorized_overtime = overtime.reconcile_authorized_overtime


def dt(value):
    return datetime.fromisoformat(value)


class OvertimeRulesTest(unittest.TestCase):
    def test_holiday_list_must_cover_work_date(self):
        self.assertTrue(holiday_list_covers("2026-08-19", "2026-01-01", "2026-12-31"))
        self.assertFalse(holiday_list_covers("2026-08-19", "2025-01-01", "2025-12-31"))
        self.assertFalse(holiday_list_covers("2026-08-19", None, None))

    def test_friday_shift_uses_custom_end_time(self):
        start, end = get_shift_window(
            "2026-08-21",
            "08:00:00",
            "17:00:00",
            friday_end_time="15:00:00",
        )
        self.assertEqual(start, dt("2026-08-21T08:00:00"))
        self.assertEqual(end, dt("2026-08-21T15:00:00"))

    def test_overnight_shift_ends_next_day(self):
        start, end = get_shift_window("2026-08-19", "22:00:00", "06:00:00")
        self.assertEqual(start, dt("2026-08-19T22:00:00"))
        self.assertEqual(end, dt("2026-08-20T06:00:00"))

    def test_classifies_holiday_and_weekly_rest_without_stacking(self):
        self.assertEqual(
            classify_workday(is_shift_workday=True, has_legal_holiday=False),
            REGULAR_DAY,
        )
        self.assertEqual(
            classify_workday(is_shift_workday=True, has_legal_holiday=True),
            LEGAL_HOLIDAY,
        )
        self.assertEqual(
            classify_workday(is_shift_workday=False, has_legal_holiday=False),
            WEEKLY_REST,
        )
        self.assertEqual(
            classify_workday(is_shift_workday=False, has_legal_holiday=True),
            HOLIDAY_ON_WEEKLY_REST,
        )

    def test_late_punch_without_an_authorized_window_is_not_counted(self):
        result = reconcile_authorized_overtime(
            authorization_start=dt("2026-08-19T18:00:00"),
            authorization_end=dt("2026-08-19T20:00:00"),
            maximum_hours=2,
            checkins=[
                {"time": "2026-08-19T08:00:00", "accion": "Inicio Jornada"},
                {"time": "2026-08-19T17:30:00", "accion": "Fin Jornada"},
            ],
            day_classification=REGULAR_DAY,
            shift_start=dt("2026-08-19T08:00:00"),
            shift_end=dt("2026-08-19T17:00:00"),
        )
        self.assertEqual(result["verified_hours"], 0)

    def test_regular_overtime_uses_only_time_outside_shift_and_honors_cap(self):
        result = reconcile_authorized_overtime(
            authorization_start=dt("2026-08-19T16:30:00"),
            authorization_end=dt("2026-08-19T21:00:00"),
            maximum_hours=2,
            checkins=[
                {"time": "2026-08-19T08:00:00", "accion": "Inicio Jornada"},
                {"time": "2026-08-19T20:30:00", "accion": "Fin Jornada"},
            ],
            day_classification=REGULAR_DAY,
            shift_start=dt("2026-08-19T08:00:00"),
            shift_end=dt("2026-08-19T18:00:00"),
        )
        self.assertEqual(result["verified_hours"], 2)
        self.assertEqual(result["regular_35_hours"], 2)

    def test_break_time_is_not_counted(self):
        result = reconcile_authorized_overtime(
            authorization_start=dt("2026-08-19T18:00:00"),
            authorization_end=dt("2026-08-19T22:00:00"),
            maximum_hours=4,
            checkins=[
                {"time": "2026-08-19T18:00:00", "accion": "Inicio Jornada"},
                {"time": "2026-08-19T19:00:00", "accion": "Inicio Break"},
                {"time": "2026-08-19T19:30:00", "accion": "Fin Break"},
                {"time": "2026-08-19T21:30:00", "accion": "Fin Jornada"},
            ],
            day_classification=LEGAL_HOLIDAY,
        )
        self.assertEqual(result["verified_hours"], 3)
        self.assertEqual(result["holiday_100_hours"], 3)
        self.assertEqual(result["night_hours"], 0.5)

    def test_weekly_rest_keeps_separate_settlement_category(self):
        result = reconcile_authorized_overtime(
            authorization_start=dt("2026-08-23T08:00:00"),
            authorization_end=dt("2026-08-23T12:00:00"),
            maximum_hours=4,
            checkins=[
                {"time": "2026-08-23T08:00:00", "log_type": "IN"},
                {"time": "2026-08-23T12:00:00", "log_type": "OUT"},
            ],
            day_classification=WEEKLY_REST,
        )
        self.assertEqual(result["weekly_rest_hours"], 4)
        self.assertEqual(result["holiday_100_hours"], 0)

    def test_holiday_on_weekly_rest_is_counted_once(self):
        result = reconcile_authorized_overtime(
            authorization_start=dt("2026-08-16T08:00:00"),
            authorization_end=dt("2026-08-16T12:00:00"),
            maximum_hours=4,
            checkins=[
                {"time": "2026-08-16T08:00:00", "log_type": "IN"},
                {"time": "2026-08-16T12:00:00", "log_type": "OUT"},
            ],
            day_classification=HOLIDAY_ON_WEEKLY_REST,
        )
        self.assertEqual(result["verified_hours"], 4)
        self.assertEqual(result["weekly_rest_hours"], 0)
        self.assertEqual(result["holiday_100_hours"], 4)

    def test_regular_hours_cross_from_35_to_100_percent_band(self):
        result = reconcile_authorized_overtime(
            authorization_start=dt("2026-08-19T18:00:00"),
            authorization_end=dt("2026-08-19T22:00:00"),
            maximum_hours=4,
            checkins=[
                {"time": "2026-08-19T18:00:00", "log_type": "IN"},
                {"time": "2026-08-19T22:00:00", "log_type": "OUT"},
            ],
            day_classification=REGULAR_DAY,
            shift_start=dt("2026-08-19T08:00:00"),
            shift_end=dt("2026-08-19T18:00:00"),
            approved_regular_overtime_before=22,
        )
        self.assertEqual(result["regular_35_hours"], 2)
        self.assertEqual(result["regular_100_hours"], 2)

    def test_incomplete_punch_pair_never_invents_hours(self):
        result = reconcile_authorized_overtime(
            authorization_start=dt("2026-08-19T18:00:00"),
            authorization_end=dt("2026-08-19T20:00:00"),
            maximum_hours=2,
            checkins=[{"time": "2026-08-19T18:00:00", "log_type": "IN"}],
            day_classification=LEGAL_HOLIDAY,
        )
        self.assertEqual(result["verified_hours"], 0)
        self.assertTrue(result["warnings"])

    def test_unknown_checkin_action_is_reported_and_not_counted(self):
        result = reconcile_authorized_overtime(
            authorization_start=dt("2026-08-19T18:00:00"),
            authorization_end=dt("2026-08-19T20:00:00"),
            maximum_hours=2,
            checkins=[{"time": "2026-08-19T18:00:00", "accion": "Manual"}],
            day_classification=LEGAL_HOLIDAY,
        )
        self.assertEqual(result["verified_hours"], 0)
        self.assertIn("Unrecognized", result["warnings"][0])

    def test_duplicate_start_discards_ambiguous_time_instead_of_inventing_it(self):
        result = reconcile_authorized_overtime(
            authorization_start=dt("2026-08-19T18:00:00"),
            authorization_end=dt("2026-08-19T22:00:00"),
            maximum_hours=4,
            checkins=[
                {"time": "2026-08-19T18:00:00", "accion": "Inicio Jornada"},
                {"time": "2026-08-19T19:30:00", "accion": "Fin Break"},
                {"time": "2026-08-19T21:30:00", "accion": "Fin Jornada"},
            ],
            day_classification=LEGAL_HOLIDAY,
        )
        self.assertEqual(result["verified_hours"], 2)
        self.assertIn("Duplicate start", result["warnings"][0])


if __name__ == "__main__":
    unittest.main()
