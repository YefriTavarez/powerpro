# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe
from powerpro.controllers.arte_original import sync_with_producto_del_cliente


def execute():
    doctype = "Arte Original"
    for arte in frappe.get_all(doctype):
        sync_with_producto_del_cliente(
            frappe.get_doc(doctype, arte.name)
        )
