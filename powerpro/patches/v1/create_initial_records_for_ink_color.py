# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import click
import frappe


def execute():
    for record in cmyk_records:
        create_new_ink_color(record)

    
def create_new_ink_color(record):
    click.secho(f"Creating {record.get('name')}...", fg="blue")

    doctype = "Ink Color"

    if frappe.db.exists(doctype, record.get("name")):
        click.secho(f"{record.get('name')} already exists... updating!", fg="yellow")
        doc = frappe.get_doc(doctype, record.get("name"))
    else:
        click.secho(f"{record.get('name')} does not exist... creating!", fg="yellow")
        doc = frappe.new_doc(doctype)

    doc.update(record)

    if doc.is_new():
        try:
            doc.insert()
        except frappe.exceptions.ValidationError:
            click.secho(f"There was an error creating {record.get('name')}!", fg="red")
        else:
            click.secho(f"{record.get('name')} created!", fg="green")
    else:
        try:
            doc.save()
        except frappe.exceptions.ValidationError:
            click.secho(f"There was an error updating {record.get('name')}!", fg="red")
        else:
            click.secho(f"{record.get('name')} updated!", fg="green")


cmyk_records = [
    {
        "currency": "DOP",
        "doctype": "Ink Color",
        "hexadecimal_color": "#000000",
        "ink_name": "Black",
        "ink_type": "Process",
        "name": "Black",
        "rate_per_kg": 1200.0,
    },
    {
        "currency": "DOP",
        "doctype": "Ink Color",
        "hexadecimal_color": "#00FFFF",
        "ink_name": "Cyan",
        "ink_type": "Process",
        "name": "Cyan",
        "rate_per_kg": 1200.0,
    },
    {
        "currency": "DOP",
        "doctype": "Ink Color",
        "hexadecimal_color": "#FF00FF",
        "ink_name": "Magenta",
        "ink_type": "Process",
        "name": "Magenta",
        "rate_per_kg": 1200.0,
    },
    {
        "currency": "DOP",
        "doctype": "Ink Color",
        "hexadecimal_color": "#FFFF00",
        "ink_name": "Yellow",
        "ink_type": "Process",
        "name": "Yellow",
        "rate_per_kg": 1200.0,
    },
]
