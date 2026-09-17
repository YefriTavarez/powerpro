"""Explicit Development-only runner; all test data rolls back, no commits, jobs or email."""
import argparse
import os
import unittest
from unittest.mock import patch
import frappe

parser=argparse.ArgumentParser()
parser.add_argument('--site',required=True)
parser.add_argument('--confirm-development',action='store_true',required=True)
args=parser.parse_args()
if args.site != 'igcaribe.fortabs.com':
    raise SystemExit('This runner is restricted to igcaribe.fortabs.com Development.')
frappe.init(site=args.site,sites_path=os.getcwd());frappe.connect();frappe.set_user('Administrator')
if not frappe.conf.get('developer_mode'):
    frappe.destroy();raise SystemExit('developer_mode is required.')
os.environ['POWERPRO_SUPPLEMENTS_DEV']='1'
frappe.flags.in_test=True

def prohibited(*args,**kwargs):raise AssertionError('Test cannot commit, email, or enqueue jobs')

try:
    suite=unittest.defaultTestLoader.discover('../apps/powerpro/tests',pattern='test_employee_supplement*.py')
    with patch.object(frappe.db,'commit',prohibited),patch.object(frappe,'sendmail',prohibited),patch.object(frappe,'enqueue',prohibited):
        result=unittest.TextTestRunner(verbosity=2).run(suite)
finally:
    frappe.db.rollback();frappe.clear_cache();frappe.destroy()
raise SystemExit(not result.wasSuccessful())
