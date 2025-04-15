# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_item_series(doctype, txt, searchfield="name", start=0, page_len=20, filters=None):
    """Query to fetch Item Series based on filters."""
    searchstr = "%%"
    if txt:
        searchstr = f"%{txt}%"

    if filters is None:
        filters = {}

    if not isinstance(filters, dict):
        frappe.msgprint("Please provide a dictionary as filters.", alert=True)
        return []

    if "item_name" not in filters:
        frappe.msgprint("Please provide an item name to search for Item Series.", alert=True)
        return []

    return frappe.db.sql(
        f"""
        SELECT
            parent.serie
        FROM
            `tabItem Series` AS parent
        INNER JOIN
            `tabItem Name Link` AS child
            ON child.parenttype = "Item Series"
            AND child.parentfield = "item_names"
            AND child.parent = parent.name
        WHERE
            child.item_name = {filters['item_name']!r}
            AND parent.serie LIKE {searchstr!r}
        """,
        as_list=True
    )