# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt


import click
import frappe


def execute():
	if not frappe.db.exists(
		"DocType", "Coating Type"
	):	frappe.reload_doctype("Coating Type")

	records = [
		"Barniz Base Aceite Combinado (Mate/Brillo)",
		"Barniz UV Combinado (Mate/Brillo)",
		"Barniz UV Selectivo Mate",
		"Barniz UV Selectivo Brillo",
		"Barniz UV Brillo",
		"Barniz UV Mate",
		"Barniz Base Aceite Brillo",
		"Barniz Base Aceite Mate",
		"Barniz Base Agua Mate",
		"Barniz Base Agua Brillo"
	]

	for record in records:
		create_new_coating_type(record)


def create_new_coating_type(coating_type):
	click.secho(f"Creating {coating_type}...", fg="blue")

	doctype = "Coating Type"

	if frappe.db.exists(doctype, coating_type):
		click.secho(f"{coating_type} already exists!", fg="yellow")
		return

	doc = frappe.new_doc(doctype)
	doc.coating_type = coating_type

	try:
		doc.insert()
	except frappe.exceptions.ValidationError:
		click.secho(f"There was an error creating {coating_type}!", fg="red")
	else:
		click.secho(f"{coating_type} created!", fg="green")
