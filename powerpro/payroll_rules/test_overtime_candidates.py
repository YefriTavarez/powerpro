import sys
import types
import unittest
from datetime import datetime
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


RULES_DIR = Path(__file__).parent
powerpro_package = types.ModuleType("powerpro")
powerpro_package.__path__ = []
payroll_rules_package = types.ModuleType("powerpro.payroll_rules")
payroll_rules_package.__path__ = []
sys.modules.setdefault("powerpro", powerpro_package)
sys.modules.setdefault("powerpro.payroll_rules", payroll_rules_package)


def load(name, filename):
	spec = spec_from_file_location(name, RULES_DIR / filename)
	module = module_from_spec(spec)
	sys.modules[name] = module
	spec.loader.exec_module(module)
	return module


overtime = load("powerpro.payroll_rules.overtime", "overtime.py")
candidates = load(
	"powerpro.payroll_rules.overtime_candidates", "overtime_candidates.py"
)


def dt(value):
	return datetime.fromisoformat(value)


class OvertimeCandidateRulesTest(unittest.TestCase):
	def analyze(self, **overrides):
		values = {
			"checkins": [
				{"time": "2026-08-10T08:00:00", "accion": "Inicio Jornada"},
				{"time": "2026-08-10T18:30:00", "accion": "Fin Jornada"},
			],
			"day_classification": overtime.REGULAR_DAY,
			"shift_start": dt("2026-08-10T08:00:00"),
			"shift_end": dt("2026-08-10T18:00:00"),
			"threshold_minutes": 15,
			"overtime_eligible": True,
			"designation": "Operador Troquelado",
			"designation_keywords": "Operador\nAuxiliar",
		}
		values.update(overrides)
		return candidates.analyze_overtime_candidate(**values)

	def test_ready_regular_candidate_requires_threshold(self):
		result = self.analyze()
		self.assertTrue(result["has_signal"])
		self.assertEqual(result["status"], candidates.OPEN)
		self.assertEqual(result["qualifying_hours"], 0.5)
		self.assertEqual(result["late_minutes"], 30)

	def test_small_delay_is_not_a_candidate(self):
		result = self.analyze(checkins=[
			{"time": "2026-08-10T08:00:00", "log_type": "IN"},
			{"time": "2026-08-10T18:10:00", "log_type": "OUT"},
		])
		self.assertFalse(result["has_signal"])
		self.assertIsNone(result["status"])

	def test_noneligible_plant_employee_is_routed_to_eligibility_review(self):
		result = self.analyze(overtime_eligible=False)
		self.assertEqual(result["status"], candidates.ELIGIBILITY_PENDING)

	def test_legal_holiday_is_in_scope_even_without_plant_designation(self):
		result = self.analyze(
			day_classification=overtime.HOLIDAY_ON_WEEKLY_REST,
			overtime_eligible=False,
			designation="Accountant",
		)
		self.assertTrue(result["in_scope"])
		self.assertEqual(result["status"], candidates.ELIGIBILITY_PENDING)
		self.assertEqual(result["qualifying_hours"], 10.5)

	def test_weekly_rest_alone_is_not_automatically_surfaced(self):
		result = self.analyze(day_classification=overtime.WEEKLY_REST)
		self.assertFalse(result["has_signal"])

	def test_missing_start_is_visible_but_requires_checkin_review(self):
		result = self.analyze(checkins=[
			{"time": "2026-08-10T19:00:00", "accion": "Fin Jornada"},
		])
		self.assertTrue(result["has_signal"])
		self.assertEqual(result["status"], candidates.NEEDS_CHECKIN_REVIEW)
		self.assertEqual(result["qualifying_hours"], 0)

	def test_break_out_is_not_mistaken_for_end_of_shift_out(self):
		result = self.analyze(checkins=[
			{"time": "2026-08-10T08:00:00", "accion": "Inicio Jornada"},
			{"time": "2026-08-10T18:30:00", "accion": "Inicio Break"},
		])
		self.assertFalse(result["has_signal"])
		self.assertIsNone(result["last_valid_out"])

	def test_exact_duplicate_punch_does_not_corrupt_otherwise_ready_evidence(self):
		result = self.analyze(checkins=[
			{"time": "2026-08-10T08:00:00", "accion": "Inicio Jornada"},
			{"time": "2026-08-10T18:30:00", "accion": "Fin Jornada"},
			{"time": "2026-08-10T18:30:00", "accion": "Fin Jornada"},
		])
		self.assertEqual(result["status"], candidates.OPEN)
		self.assertIn("Ignored 1 exact duplicate", result["warnings"][-1])

	def test_overnight_shift_uses_following_day_out(self):
		result = self.analyze(
			checkins=[
				{"time": "2026-08-10T22:00:00", "log_type": "IN"},
				{"time": "2026-08-11T06:45:00", "log_type": "OUT"},
			],
			shift_start=dt("2026-08-10T22:00:00"),
			shift_end=dt("2026-08-11T06:00:00"),
		)
		self.assertEqual(result["status"], candidates.OPEN)
		self.assertEqual(result["qualifying_hours"], 0.75)

	def test_employee_date_dedupe_key_is_stable(self):
		self.assertEqual(
			candidates.candidate_dedupe_key("EMP-001", "2026-08-10 00:00:00"),
			"EMP-001::2026-08-10",
		)

	def test_completed_refresh_invalidates_reviewable_candidate_without_signal(self):
		self.assertEqual(
			candidates.get_candidate_refresh_action(
				existing_status=candidates.OPEN,
				evaluation_complete=True,
				candidate_present=False,
			),
			"invalidate",
		)

	def test_incomplete_evaluation_never_invalidates_candidate(self):
		self.assertIsNone(
			candidates.get_candidate_refresh_action(
				existing_status=candidates.OPEN,
				evaluation_complete=False,
				candidate_present=False,
			)
		)

	def test_final_decision_is_never_overwritten_by_refresh(self):
		self.assertIsNone(
			candidates.get_candidate_refresh_action(
				existing_status="Approved Cash",
				evaluation_complete=True,
				candidate_present=False,
			)
		)

	def test_existing_overtime_supersedes_reviewable_candidate(self):
		self.assertEqual(
			candidates.get_candidate_refresh_action(
				existing_status=candidates.NEEDS_CHECKIN_REVIEW,
				evaluation_complete=True,
				candidate_present=True,
				existing_overtime=True,
			),
			"supersede",
		)

	def test_overnight_shift_is_not_complete_before_scheduled_end(self):
		self.assertFalse(
			candidates.is_shift_evaluation_complete(
				"2026-08-11T06:00:00",
				"2026-08-11T05:59:59",
			)
		)

	def test_shift_is_complete_at_scheduled_end(self):
		self.assertTrue(
			candidates.is_shift_evaluation_complete(
				"2026-08-11T06:00:00",
				"2026-08-11T06:00:00",
			)
		)


if __name__ == "__main__":
	unittest.main()
