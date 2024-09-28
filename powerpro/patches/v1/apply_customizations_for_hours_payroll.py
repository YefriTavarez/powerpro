import frappe
import json


file = "/home/frappe/frappe-bench/apps/powerpro/powerpro/patches/v1/apply_customizations_for_hours_payroll.json"


def execute():
    with open(file) as f:
        data = json.load(f)

    custom_fields = data.get("custom_fields")
    property_setters = data.get("property_setters")

    if custom_fields:
        create_custom_fields(custom_fields)

    if property_setters:
        create_property_setters(property_setters)


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


def create_property_setters(property_setters):
    doctype = "Property Setter"

    for setter in property_setters:
        if name := frappe.db.exists(doctype, setter.get("name")):
            doc = frappe.get_doc(doctype, name)
        else:
            doc = frappe.new_doc(doctype)

        doc.update(setter)
        doc.db_update()
        print(f"Property Setter {doc.name} created")