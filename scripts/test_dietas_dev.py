"""Opt-in rollback-only Frappe integration runner for a verified development site."""
import argparse
import os
from pathlib import Path
import runpy
import sys
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

import frappe

parser = argparse.ArgumentParser()
parser.add_argument('--site', required=True)
parser.add_argument('--company', help='Existing company for rollback-only test fixtures')
parser.add_argument('--sites-path', required=True)
parser.add_argument('--confirm-development', action='store_true', required=True)
args = parser.parse_args()
if args.site in ('igcaribe.com', 'igcaribe.erpnext.com'):
    raise SystemExit('Refusing the known production site.')
frappe.init(site=args.site, sites_path=args.sites_path)
if urlsplit(frappe.conf.get('host_name') or '').hostname in ('igcaribe.com','www.igcaribe.com'):
    raise SystemExit('Refusing the production hostname.')
frappe.connect()
os.environ['POWERPRO_DIETA_DEV_TESTS'] = '1'
if args.company:
    os.environ['POWERPRO_DIETA_TEST_COMPANY'] = args.company


def prohibited(*args, **kwargs):
    raise AssertionError('The isolated dieta integration test cannot commit or send mail')


try:
    namespace = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'tests/test_dietas_db.py'), run_name='dieta_db_suite')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(namespace['DietaDatabaseTest'])
    # Error Log uses deferred writes outside the transaction on Frappe v15.
    with patch.object(frappe.db, 'commit', prohibited), patch.object(frappe, 'sendmail', prohibited), patch.object(frappe, 'enqueue', return_value=None), patch.object(frappe, 'log_error', return_value=None):
        result = unittest.TextTestRunner(verbosity=2).run(suite)
finally:
    frappe.db.rollback()
    frappe.destroy()
sys.exit(not result.wasSuccessful())
