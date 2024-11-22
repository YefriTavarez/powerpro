# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt


import click
import frappe


def execute():
	records = [
		"Brillo",
		"Mate",
		"Soft-Touch",
	]

	for record in records:
		create_new_lamination_type(record)


def create_new_lamination_type(lamination_type):
	click.secho(f"Creating {lamination_type}...", fg="blue")

	doctype = "Lamination Type"

	if frappe.db.exists(doctype, lamination_type):
		click.secho(f"{lamination_type} already exists!", fg="yellow")
		return

	doc = frappe.new_doc(doctype)
	doc.lamination_type = lamination_type

	try:
		doc.insert()
	except frappe.exceptions.ValidationError:
		click.secho(f"There was an error creating {lamination_type}!", fg="red")
	else:
		click.secho(f"{lamination_type} created!", fg="green")
