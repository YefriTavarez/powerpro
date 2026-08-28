import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from powerpro.controllers import overtime_candidates as candidates


def result_template():
	return {
		"skipped_existing_overtime": 0,
		"superseded": 0,
		"invalidated": 0,
		"stale_candidates": [],
	}


class OvertimeCandidateRefreshControllerTest(unittest.TestCase):
	def setUp(self):
		self.employee = SimpleNamespace(
			name="HR-EMP-0001",
			employee_name="Employee One",
		)

	def test_preview_reports_invalidation_without_saving(self):
		result = result_template()
		existing_candidate = SimpleNamespace(name="OT-CAND-0001", status="Open")
		with (
			patch.object(candidates, "_get_existing_overtime_record", return_value=None),
			patch.object(candidates, "_invalidate_stale_candidate") as invalidate,
		):
			candidates._handle_stale_candidate(
				result,
				self.employee,
				"2026-08-15",
				evaluation_complete=True,
				dry_run=True,
				existing_candidate=existing_candidate,
			)

		self.assertEqual(result["invalidated"], 1)
		self.assertEqual(result["stale_candidates"][0]["action"], "invalidate")
		invalidate.assert_not_called()

	def test_incomplete_evaluation_does_not_invalidate(self):
		result = result_template()
		existing_candidate = SimpleNamespace(name="OT-CAND-0001", status="Open")
		with (
			patch.object(candidates, "_get_existing_overtime_record", return_value=None),
			patch.object(candidates, "_invalidate_stale_candidate") as invalidate,
		):
			candidates._handle_stale_candidate(
				result,
				self.employee,
				"2026-08-15",
				evaluation_complete=False,
				dry_run=False,
				existing_candidate=existing_candidate,
			)

		self.assertEqual(result["invalidated"], 0)
		self.assertEqual(result["stale_candidates"], [])
		invalidate.assert_not_called()

	def test_final_candidate_is_not_invalidated(self):
		doc = MagicMock()
		doc.status = "Approved Cash"
		with patch.object(candidates.frappe, "get_doc", return_value=doc):
			changed = candidates._invalidate_stale_candidate("OT-CAND-0001")

		self.assertFalse(changed)
		doc.save.assert_not_called()

	def test_reviewable_candidate_is_invalidated_with_audit_fields(self):
		doc = MagicMock()
		doc.status = "Open"
		doc.flags = SimpleNamespace()
		with (
			patch.object(candidates.frappe, "get_doc", return_value=doc),
			patch.object(candidates, "now_datetime", return_value="2026-08-28 12:00:00"),
		):
			changed = candidates._invalidate_stale_candidate("OT-CAND-0001")

		self.assertTrue(changed)
		self.assertEqual(doc.status, "Invalid Check-in")
		self.assertTrue(doc.decision_reason)
		self.assertEqual(doc.decided_on, "2026-08-28 12:00:00")
		self.assertTrue(doc.flags.generated_by_overtime_scanner)
		doc.save.assert_called_once_with(ignore_permissions=True)


if __name__ == "__main__":
	unittest.main()
