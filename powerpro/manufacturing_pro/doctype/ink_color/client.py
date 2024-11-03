# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def get_all_ink_colors():
	return frappe.get_all("Ink Color", pluck="name")
