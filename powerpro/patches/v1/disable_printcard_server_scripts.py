# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


def execute():
	doctype = "Server Script"

	doclist = [
		"PrintCard - Before Insert",
		"PrintCard - Before Delete",
		"PrintCard - After Insert",
		"PrintCard - Before Save",
		"PrintCard - After Save"
	]

	for name in doclist:
		if frappe.db.exists(doctype, name):
			doc = frappe.get_doc(doctype, name)
			doc.disabled = 1
			doc.save()
			print(f"Server Script {doc.name} disabled")
		else:
			print(f"Server Script {doc.name} not found")
