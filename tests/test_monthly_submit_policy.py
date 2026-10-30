"""Submit-adapter unit tests using Frappe stubs; no site or database is needed.

Run directly with: python tests/test_monthly_submit_policy.py
The shared payroll calculations and site Server Script have separate numerical tests.
"""

import ast
import json
from pathlib import Path
from types import SimpleNamespace
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "powerpro/controllers/salary_slip/monthly.py"
POLICY = "IGC - Topes TSS - Aplicar a Recibo V1"
MISSING = "Falta confirmar el período previo: 2026-10-01 a 2026-10-15"


class ValidationError(Exception):
    pass


def adapter_functions(frappe_stub, settings, lock):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name in {"before_submit", "apply_site_settlement_adjustments"}]
    if len(selected) != 2:
        raise AssertionError("Both actual adapter functions must be tested")
    namespace = {"frappe": frappe_stub, "json": json,
                 "settings_for": settings, "lock_employee": lock}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(SOURCE), "exec"), namespace)
    return namespace


class MonthlySubmitPolicyTest(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.exists = True
        self.script = SimpleNamespace(disabled=0, script_type="DocType Event",
                                      reference_doctype="Salary Slip", execute_doc=self.adjust)
        self.frappe = SimpleNamespace(
            db=SimpleNamespace(exists=self.script_exists), get_doc=self.get_script,
            throw=self.throw,
        )
        self.settings = True
        self.functions = adapter_functions(self.frappe, lambda doc: self.settings, self.lock)
        self.current_issues = [MISSING]
        self.previous = {"AFP": 0, "ARS": 0}
        self.doc = SimpleNamespace(monthly_settlement_snapshot=None,
                                   calculate_net_pay=self.recalculate, locked=False)

    def throw(self, message):
        raise ValidationError(message)

    def lock(self, doc):
        self.events.append("lock")
        doc.locked = True

    def recalculate(self):
        self.assertTrue(self.doc.locked)
        self.events.append("recalculate")
        self.doc.monthly_settlement_snapshot = json.dumps({
            "issues": self.current_issues, "previous": self.previous,
        })

    def script_exists(self, doctype, name):
        self.assertEqual((doctype, name), ("Server Script", POLICY))
        self.events.append("exists")
        return self.exists

    def get_script(self, doctype, name):
        self.assertEqual((doctype, name), ("Server Script", POLICY))
        self.events.append("load")
        return self.script

    def adjust(self, doc):
        self.assertTrue(doc.locked)
        self.assertEqual(self.events[:2], ["lock", "recalculate"])
        self.events.append("adjust")
        result = json.loads(doc.monthly_settlement_snapshot)
        result["issues"] = [issue for issue in result["issues"] if issue != MISSING]
        result["salary"] = 31000
        result["applied"] = {"AFP": 889.70 - result["previous"]["AFP"],
                             "ARS": 942.40 - result["previous"]["ARS"]}
        doc.monthly_settlement_snapshot = json.dumps(result)

    def submit(self):
        self.functions["before_submit"](self.doc)

    def test_adjustment_runs_after_locked_recalculation_before_issue_check(self):
        self.submit()
        self.assertEqual(self.events, ["lock", "recalculate", "exists", "load", "adjust"])
        result = json.loads(self.doc.monthly_settlement_snapshot)
        self.assertEqual(result["issues"], [])
        self.assertEqual(result["salary"], 31000)

    def test_missing_script_keeps_native_validation(self):
        self.exists = False
        with self.assertRaisesRegex(ValidationError, MISSING):
            self.submit()
        self.assertEqual(self.events, ["lock", "recalculate", "exists"])

    def test_disabled_script_keeps_native_validation(self):
        self.script.disabled = 1
        with self.assertRaisesRegex(ValidationError, MISSING):
            self.submit()
        self.assertNotIn("adjust", self.events)

    def test_unrelated_issues_still_block_submission(self):
        self.current_issues.append("Otro bloqueo del acumulado")
        with self.assertRaisesRegex(ValidationError, "Otro bloqueo del acumulado"):
            self.submit()

    def test_wrong_script_type_fails_closed(self):
        self.script.script_type = "API"
        with self.assertRaisesRegex(ValidationError, "Server Script de eventos"):
            self.submit()
        self.assertNotIn("adjust", self.events)

    def test_wrong_reference_doctype_fails_closed(self):
        self.script.reference_doctype = "Employee"
        with self.assertRaisesRegex(ValidationError, "Salary Slip"):
            self.submit()
        self.assertNotIn("adjust", self.events)

    def test_policy_exception_is_not_swallowed(self):
        def failure(doc):
            raise ValidationError("Error de la política fiscal")
        self.script.execute_doc = failure
        with self.assertRaisesRegex(ValidationError, "Error de la política fiscal"):
            self.submit()

    def test_feature_disabled_keeps_original_early_return(self):
        self.settings = False
        self.submit()
        self.assertEqual(self.events, [])

    def test_successful_native_result_works_without_site_policy(self):
        self.exists = False
        self.current_issues = []
        self.submit()
        self.assertEqual(json.loads(self.doc.monthly_settlement_snapshot)["issues"], [])

    def test_positive_previous_withholding_reaches_shared_policy(self):
        self.previous = {"AFP": 100, "ARS": 200}
        self.submit()
        result = json.loads(self.doc.monthly_settlement_snapshot)
        self.assertEqual(result["previous"], self.previous)
        self.assertAlmostEqual(result["applied"]["AFP"], 789.70)
        self.assertAlmostEqual(result["applied"]["ARS"], 742.40)


if __name__ == "__main__":
    unittest.main()
