# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt


import frappe


def execute():
	doctype = "DocType"
	name = "Item Generator"
	if name := frappe.db.exists(doctype, name):
		doc = frappe.get_doc(doctype, name)
	else:
		print(f"DocType {doctype} {name} does not exist... skipping")
		return
	
	doc.custom = 1
	doc.db_update()
	print(f"DocType {doctype} {name} updated to custom")
