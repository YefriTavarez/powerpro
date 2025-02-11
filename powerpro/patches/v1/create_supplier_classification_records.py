# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt


import frappe


def execute():
	# Create Supplier Classification Records
	create_supplier_classification_records()


def create_supplier_classification_records():
	records = [
		{
			"name": "Proveedores Físicos Locales",
			"type": "Individual"
		},
		{
			"name": "Proveedores Jurídicos Locales",
			"type": "Company"	
		},
		{
			"name": "Proveedores Internacionales",
			"type": "Company"
		},
		{
			"name": "Proveedores Informales",
			"type": "Individual"
		},
	]

	for record in records:
		if not frappe.db.exists("Supplier Classification", record.get("name")):
			frappe.get_doc({
				"doctype": "Supplier Classification",
				"supplier_classification": record.get("name"),
				"supplier_type": record.get("type")
			}).insert()
