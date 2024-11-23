# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def get_foil_color_options():
	return frappe.get_all("Foil Color", pluck="name")
