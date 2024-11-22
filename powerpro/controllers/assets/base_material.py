# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt


import frappe


@frappe.whitelist()
def get_base_material_details(name):
	doctype = "Base Material"
	return frappe.get_doc(doctype, name) \
		.as_dict()
