# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt


import frappe


def execute():
	doctype = "Project Template"
	pluck = "name"

	for name in frappe.get_all(doctype, pluck=pluck):
		doc = frappe.get_doc(doctype, name)
		doc.project_docfields = []

		doc.set_project_docfields()
		doc.flags.ignore_mandatory = True
		doc.save()
