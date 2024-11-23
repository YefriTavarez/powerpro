# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def get_gluing_type_options():
	doctype = "Gluing Type"
	return frappe.get_all(doctype, pluck="name")
