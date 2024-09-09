# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


def execute():
    fieldlist = [
        "Item-custom_item_group_5",
        "Item-custom_item_group_4",
        "Item-custom_item_group_3",
        "Item-custom_item_group_2",
        "Item-custom_item_group_1"
    ]


    for name in fieldlist:
        doctype = "Custom Field"

        # future proof check
        if not frappe.db.exists(doctype, name):
            continue

        doc = frappe.get_doc(doctype, name)

        if not doc.read_only_depends_on:
            doc.read_only_depends_on = "eval:!doc.__islocal"
            doc.save()
