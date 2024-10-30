import frappe
import json

file = "/home/frappe/frappe-bench/apps/powerpro/powerpro/patches/v1/igc_8_refactor_fields.json"


def execute():
    delete_custom_field()
    update_custom_fields()


def delete_custom_field():
    doctype = "Custom Field"
    name = "Salary Slip-health_insurance_provider"

    if name := frappe.db.exists(doctype, name):
        frappe.delete_doc(doctype, name)


def update_custom_fields():
    doctype = "Custom Field"

    with open(file) as f:
        data = json.load(f)

    custom_fields = data.get("custom_fields")

    for field in custom_fields:
        if name := frappe.db.exists(doctype, field.get("name")):
            doc = frappe.get_doc(doctype, name)
        else:
            doc = frappe.new_doc(doctype)

        doc.update(field)
        doc.db_update()
        print(f"Custom Field {doc.label} created")

