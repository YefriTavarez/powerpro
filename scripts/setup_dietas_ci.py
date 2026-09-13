"""Create only the accounting prerequisites needed by Dieta CI tests."""
import os
from pathlib import Path

import frappe

if os.environ.get("GITHUB_ACTIONS") != "true":
    raise SystemExit("This fixture initializer is restricted to GitHub Actions.")

sites = Path("/home/runner/frappe-bench/sites")
os.chdir(sites)
frappe.init(site="test_site", sites_path=str(sites))
if frappe.conf.get("host_name"):
    raise SystemExit("The disposable CI site must not have a public hostname.")
frappe.connect()
try:
    frappe.set_user("Administrator")
    frappe.flags.in_test = True
    if not frappe.db.exists("Company", "_Test Company"):
        frappe.get_doc({
            "doctype": "Company",
            "company_name": "_Test Company",
            "abbr": "_TC",
            "country": "Dominican Republic",
            "default_currency": "DOP",
            "create_chart_of_accounts_based_on": "Standard Template",
            "chart_of_accounts": "Standard",
        }).insert()
    if not frappe.db.exists("Mode of Payment", {"type": "Cash", "enabled": 1}):
        frappe.get_doc({
            "doctype": "Mode of Payment", "mode_of_payment": "Dieta CI Cash",
            "type": "Cash", "enabled": 1,
        }).insert()
    assert frappe.db.exists("Company", "_Test Company")
    frappe.db.commit()
    print("Dieta CI company and cash payment method are ready.")
finally:
    frappe.db.rollback()
    frappe.destroy()
