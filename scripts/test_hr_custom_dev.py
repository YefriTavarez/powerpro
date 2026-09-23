"""Run HR migration tests on an explicitly designated isolated Development site."""
import argparse
import os
import unittest
from pathlib import Path
from unittest.mock import patch

import frappe

parser = argparse.ArgumentParser()
parser.add_argument("--site", required=True)
parser.add_argument("--confirm-development", action="store_true", required=True)
args = parser.parse_args()
frappe.init(site=args.site, sites_path=os.getcwd())
if not frappe.conf.get("developer_mode") or not frappe.conf.get("powerpro_hr_rehearsal"):
    raise SystemExit("Requires developer_mode and powerpro_hr_rehearsal on an isolated site.")
frappe.connect()
frappe.set_user("Administrator")
frappe.get_hooks()
os.environ["POWERPRO_HR_CUSTOM_DEV"] = "1"


def prohibited(*args, **kwargs):
    raise AssertionError("HR migration regression cannot commit, send email, or enqueue jobs")


try:
    suite = unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parents[1] / "tests"),
                                              pattern="test_hr_custom_metadata.py")
    with patch.object(frappe.db, "commit", prohibited), patch.object(frappe, "sendmail", prohibited), patch.object(frappe, "enqueue", prohibited):
        result = unittest.TextTestRunner(verbosity=2).run(suite)
finally:
    frappe.db.rollback()
    frappe.destroy()
raise SystemExit(not result.wasSuccessful() or bool(result.skipped))
