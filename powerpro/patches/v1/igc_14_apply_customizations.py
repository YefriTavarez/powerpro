import frappe
import json


file = "/home/frappe/frappe-bench/apps/powerpro/powerpro/patches/v1/igc_14_apply_customizations.json"


def execute():
    with open(file) as f:
        data = json.load(f)

    custom_fields = data.get("custom_fields")

    if custom_fields:
        create_custom_fields(custom_fields)


def create_custom_fields(custom_fields):
    doctype = "Custom Field"

    for field in custom_fields:
        if name := frappe.db.exists(doctype, field.get("name")):
            doc = frappe.get_doc(doctype, name)
        else:
            doc = frappe.new_doc(doctype)
        # doc = frappe.new_doc(doctype)
        doc.update(field)
        doc.db_update()
        print(f"Custom Field {doc.label} created")

