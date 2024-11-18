# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt


import frappe


@frappe.whitelist()
def get_all_item_groups():
	return frappe.get_all(
		"Item Group", fields=["name", "parent_item_group", "is_group"]
	)
