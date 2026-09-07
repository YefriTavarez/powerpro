"""Run focused tests against an explicitly authorized DEV site and roll everything back."""
import argparse
import os
import sys
import unittest
from unittest.mock import patch

import frappe

parser = argparse.ArgumentParser()
parser.add_argument("--site", required=True)
parser.add_argument("--sites-path", default=os.getcwd())
parser.add_argument("--confirm-development", action="store_true", required=True)
args = parser.parse_args()
os.environ["POWERPRO_MONTHLY_DEV_INTEGRATION"] = "1"
frappe.init(site=args.site, sites_path=args.sites_path)
frappe.connect()
frappe.set_user("Administrator")


def prohibited(*args, **kwargs):
    raise AssertionError("The DEV test suite cannot commit or send email")


try:
    suite = unittest.defaultTestLoader.loadTestsFromNames([
        "powerpro.payroll_rules.test_monthly_settlement",
        "powerpro.payroll_rules.test_employer_contributions",
        "powerpro.payroll_rules.test_dominican_republic",
        "powerpro.controllers.salary_slip.test_monthly_integration",
    ])
    with patch.object(frappe.db, "commit", prohibited), patch.object(frappe, "sendmail", prohibited):
        result = unittest.TextTestRunner(verbosity=1).run(suite)
finally:
    frappe.db.rollback()
    frappe.destroy()
sys.exit(not result.wasSuccessful())
