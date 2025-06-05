# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


def get_dashboard_data(data=None):
	meta = frappe.get_meta("Project")

	private_data = frappe._dict()
	meta.add_doctype_links(private_data)

	return private_data
