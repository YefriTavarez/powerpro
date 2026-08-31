import sys
import unittest
from datetime import datetime
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


MODULE_NAME = "powerpro_overtime_work_call_rules"
SPEC = spec_from_file_location(
	MODULE_NAME, Path(__file__).with_name("overtime_work_call.py")
)
rules = module_from_spec(SPEC)
sys.modules[MODULE_NAME] = rules
SPEC.loader.exec_module(rules)


class OvertimeWorkCallRulesTest(unittest.TestCase):
	def test_builds_same_day_team_window(self):
		start, end = rules.build_authorization_window(
			"2026-08-16", "08:00:00", "14:00:00"
		)
		self.assertEqual(start, datetime.fromisoformat("2026-08-16T08:00:00"))
		self.assertEqual(end, datetime.fromisoformat("2026-08-16T14:00:00"))
		self.assertEqual(rules.requested_hours("2026-08-16", "08:00", "14:00"), 6)

	def test_builds_overnight_team_window(self):
		start, end = rules.build_authorization_window(
			"2026-12-18", "22:00:00", "02:00:00"
		)
		self.assertEqual(start, datetime.fromisoformat("2026-12-18T22:00:00"))
		self.assertEqual(end, datetime.fromisoformat("2026-12-19T02:00:00"))
		self.assertEqual(rules.requested_hours("2026-12-18", "22:00", "02:00"), 4)

	def test_completed_snapshot_tracks_full_adherence(self):
		snapshot = self.snapshot(
			verified_hours=6,
			regular_35_hours=4,
			regular_100_hours=2,
			intervals=[{"start": "2026-08-16T08:00:00", "end": "2026-08-16T14:00:00"}],
		)
		self.assertEqual(snapshot["reconciliation_status"], "Completed")
		self.assertEqual(snapshot["adherence_percent"], 100)
		self.assertEqual(snapshot["missing_hours"], 0)
		self.assertEqual(snapshot["regular_35_hours"], 4)
		self.assertEqual(snapshot["regular_100_hours"], 2)

	def test_partial_snapshot_tracks_late_arrival_and_missing_hours(self):
		snapshot = self.snapshot(
			verified_hours=5.5,
			intervals=[{"start": "2026-08-16T08:30:00", "end": "2026-08-16T14:00:00"}],
		)
		self.assertEqual(snapshot["reconciliation_status"], "Partial")
		self.assertEqual(snapshot["late_minutes"], 30)
		self.assertEqual(snapshot["missing_hours"], 0.5)

	def test_continuous_hours_beyond_call_require_review(self):
		snapshot = self.snapshot(
			verified_hours=6,
			unapproved_hours=1,
			intervals=[{"start": "2026-08-16T08:00:00", "end": "2026-08-16T14:00:00"}],
		)
		self.assertEqual(snapshot["reconciliation_status"], "Overrun")
		self.assertEqual(snapshot["unapproved_hours"], 1)

	def test_future_window_remains_scheduled(self):
		snapshot = self.snapshot(
			verified_hours=0,
			intervals=[],
			evaluation_time="2026-08-16T09:00:00",
		)
		self.assertEqual(snapshot["reconciliation_status"], "Scheduled")

	def test_ambiguous_punches_require_checkin_review(self):
		snapshot = self.snapshot(
			verified_hours=0,
			intervals=[],
			warnings=["Open work interval beginning 2026-08-16T08:00:00"],
		)
		self.assertEqual(snapshot["reconciliation_status"], "Check-in Issue")

	def snapshot(
		self,
		*,
		verified_hours,
		intervals,
		unapproved_hours=0,
		regular_35_hours=0,
		regular_100_hours=0,
		holiday_100_hours=0,
		weekly_rest_hours=0,
		night_hours=0,
		warnings=None,
		evaluation_time="2026-08-16T15:00:00",
	):
		return rules.derive_reconciliation_snapshot(
			authorization_start="2026-08-16T08:00:00",
			authorization_end="2026-08-16T14:00:00",
			maximum_hours=6,
			evaluation_time=evaluation_time,
			reconciliation={
				"verified_hours": verified_hours,
				"unapproved_hours": unapproved_hours,
				"regular_35_hours": regular_35_hours,
				"regular_100_hours": regular_100_hours,
				"holiday_100_hours": holiday_100_hours,
				"weekly_rest_hours": weekly_rest_hours,
				"night_hours": night_hours,
				"intervals": intervals,
				"warnings": warnings or [],
				"source_checkins": [
					{"time": "2026-08-16T08:00:00", "log_type": "IN"},
					{"time": "2026-08-16T14:00:00", "log_type": "OUT"},
				],
			},
		)


if __name__ == "__main__":
	unittest.main()
