# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import click
import frappe


def execute():
	records = [
		"Pegado 6 Puntos",
		"Pegado 4 Puntos",
		"Pegado Especial",
		"Pegado Fondo Automático",
		"Pegado Lineal"
	]

	for record in records:
		create_new_gluing_type(record)


def create_new_gluing_type(gluing_type):
	click.secho(f"Creating {gluing_type}...", fg="blue")

	doctype = "Gluing Type"

	if frappe.db.exists(doctype, gluing_type):
		click.secho(f"{gluing_type} already exists!", fg="yellow")
		return

	doc = frappe.new_doc(doctype)
	doc.gluing_type = gluing_type

	try:
		doc.insert()
	except frappe.exceptions.ValidationError:
		click.secho(f"There was an error creating {gluing_type}!", fg="red")
	else:
		click.secho(f"{gluing_type} created!", fg="green")
