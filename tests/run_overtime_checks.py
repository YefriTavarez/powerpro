"""Run manual-attendance and existing overtime regressions without a Frappe site."""
from pathlib import Path
import runpy
import unittest

root = Path(__file__).resolve().parents[1]
adapter = runpy.run_path(str(root / 'tests/test_manual_overtime.py'), run_name='sitefree_adapter')
loader = unittest.defaultTestLoader
suite = unittest.TestSuite([
    loader.loadTestsFromTestCase(adapter['ManualOvertimeTest']),
    loader.loadTestsFromNames([
        'powerpro.controllers.test_overtime_settlement',
        'powerpro.controllers.test_overtime_compensatory_settlement',
        'powerpro.controllers.test_overtime_cash_settlement',
    ]),
    loader.discover(str(root / 'powerpro/payroll_rules'), pattern='test_overtime*.py'),
])
result = unittest.TextTestRunner(verbosity=1).run(suite)
raise SystemExit(not result.wasSuccessful())
