# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ProductoDelCliente(Document):
    def on_update(self):
        sync_with_arte_original(self)


def sync_with_arte_original(doc):
    arte = get_arte_original(doc.name)

    if arte:
        arte.possible_items = [
            frappe.copy_doc(item)
            for item in doc.possible_items
        ]

        arte.flags.ignore_permissions = True
        arte.flags.ignore_mandatory = True
        arte.save()


def get_arte_original(name):
    doctype = "Arte Original"

    if name := frappe.db.exists(doctype, {"nombre_arte": name}):
        return frappe.get_doc(doctype, name)
    else:
        return None
