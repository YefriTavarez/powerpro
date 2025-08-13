# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import click

import frappe


def execute():
	doctype = "Project Template"
	pluck = "name"

	for name in frappe.get_all(doctype, pluck=pluck):
		click.secho(f"Processing {name}", fg="yellow")
		doc = frappe.get_doc(doctype, name)
		doc.project_docfields = []

		try:
			doc.set_project_docfields()
		except Exception as e:
			click.secho(f"Error setting project docfields for {name}: {e}", fg="red")
			continue
		else:
			doc.flags.ignore_mandatory = True
			doc.save()
			click.secho(f"Done for {name}", fg="green")

	click.secho("Done", fg="green")