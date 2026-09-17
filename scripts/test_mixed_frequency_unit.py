"""Standalone unit/contract tests: no site, database, queues or network.

Framework operations are explicit test doubles; this does not certify a deployed
HRMS controller. Run from the repository root with python scripts/test_mixed_frequency_unit.py.
"""
import datetime
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock

root = Path(__file__).resolve().parents[1]
package = types.ModuleType("powerpro")
package.__path__ = [str(root / "powerpro")]
sys.modules["powerpro"] = package  # Avoid the app's installation-time import hook.


class AttrDict(dict):
    def __getattr__(self, key):
        if key.startswith('__'):
            raise AttributeError(key)
        return self.get(key)
    __setattr__ = dict.__setitem__


frappe = types.ModuleType("frappe")
frappe._dict = AttrDict
frappe._ = lambda text: text
frappe.whitelist = lambda *a, **k: lambda method: method
for name in ("get_all", "get_cached_doc", "get_doc", "throw", "publish_realtime", "msgprint"):
    setattr(frappe, name, Mock())
frappe.get_single = Mock(return_value=AttrDict(enabled=0))
frappe.db = Mock()
frappe.session = AttrDict(user="test-user")
frappe.flags = AttrDict()
sys.modules["frappe"] = frappe
utils = types.ModuleType("frappe.utils")
utils.cint = lambda value: int(value or 0)
utils.getdate = lambda value: datetime.date.fromisoformat(str(value)[:10])
utils.flt = lambda value: float(value or 0)
utils.today = lambda: datetime.date.today().isoformat()
sys.modules["frappe.utils"] = utils

suite = unittest.defaultTestLoader.loadTestsFromNames([
    "powerpro.payroll_rules.test_mixed_frequency",
    "powerpro.controllers.test_mixed_frequency_payroll",
    "powerpro.payroll_rules.test_monthly_settlement",
    "powerpro.payroll_rules.test_employer_contributions",
    "powerpro.payroll_rules.test_dominican_republic",
])
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())
