"""Run retainer DB contracts on the explicitly named development site only.

Fixtures and every test run in rollback-only transactions. No invoice is submitted,
no schema is installed here, and HTTP/mail/background work and commit are blocked.
This proves controller/database integration, not separate-session concurrency.
"""
import argparse
import inspect
import os
from pathlib import Path
import runpy
import sys
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', required=True, choices=['igcaribe.fortabs.com'])
    parser.add_argument('--sites-path', required=True)
    parser.add_argument('--company', required=True)
    parser.add_argument('--confirm-development', required=True, choices=['igcaribe.fortabs.com'])
    args = parser.parse_args()
    if args.site != args.confirm_development:
        parser.error('Development confirmation must exactly match the site.')
    sites_path = Path(args.sites_path).resolve()
    if not (sites_path / args.site / 'site_config.json').is_file():
        parser.error('The development site configuration must exist in sites-path.')
    import frappe
    import requests
    os.chdir(sites_path)
    frappe.init(site=args.site, sites_path=str(sites_path))
    configured_host = urlsplit(frappe.conf.get('host_name') or '').hostname
    if configured_host not in (None, 'igcaribe.fortabs.com'):
        frappe.destroy()
        raise SystemExit('Unexpected configured hostname: refusing integration tests.')
    frappe.connect()
    os.environ['POWERPRO_RETAINER_DEV_TESTS'] = '1'
    os.environ['POWERPRO_RETAINER_TEST_COMPANY'] = args.company
    original_user = frappe.session.user
    original_in_test = frappe.flags.in_test

    def prohibited(*args, **kwargs):
        raise AssertionError('Rollback-only retainer tests prohibit commits, mail, jobs and HTTP.')

    try:
        if not frappe.db.exists('Company', args.company):
            raise RuntimeError('The explicit development Company does not exist.')
        # Fail early if a different Frappe version has incompatible guard APIs.
        assert 'save_point' in inspect.signature(frappe.db.rollback).parameters
        assert callable(frappe.db.savepoint)
        assert callable(frappe.sendmail) and callable(frappe.enqueue)
        frappe.flags.in_test = True
        namespace = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'tests/test_supplier_retainers_db.py'))
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(namespace['SupplierRetainerDatabaseTest'])
        with patch.object(frappe.db, 'commit', prohibited), \
             patch.object(frappe, 'sendmail', prohibited), \
             patch.object(frappe, 'enqueue', prohibited), \
             patch.object(frappe, 'log_error', return_value=None), \
             patch.object(requests.sessions.Session, 'request', prohibited):
            result = unittest.TextTestRunner(verbosity=2).run(suite)
    finally:
        frappe.db.rollback()
        frappe.set_user(original_user)
        frappe.flags.in_test = original_in_test
        frappe.destroy()
    return int(not result.wasSuccessful() or bool(result.skipped))


if __name__ == '__main__':
    sys.exit(main())
