# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_producto_del_cliente(doctype, txt, searchfield, start, page_len, filters):
    """
    Retrieve producto del cliente information based on the search text and filters.
    One of the Filters is the item which the producto del cliente is related to.

    Args:
        doctype (str): The type of document to search within.
        txt (str): The text to search for within producto del cliente.
        searchfield (str): The field to search within.
        start (int): The starting index for the search results.
        page_len (int): The number of results to return.
        filters (dict): Additional filters to apply to the search.

    Returns:
        list: A list of producto del cliente results matching the search criteria.
    """

    searchstr = "%%"
    if txt:
        searchstr = f"%{txt}%"

    if filters is None:
        filters = {}

    if isinstance(filters, list):
        frappe.msgprint("Please provide a dictionary as filters.", alert=True)
        return []

    if "item_code" not in filters:
        frappe.msgprint("Please provide an 'Item Code' to search for 'Producto del Cliente'.", alert=True)
        return []

    if "customer" not in filters:
        frappe.msgprint("Please provide a 'Customer' to search for 'Producto del Cliente'.", alert=True)
        return []

    out = frappe.db.sql(
        f"""
            Select
                parent.name,
                parent.codigo,
                parent.tipo_producto
            From
                `tabProducto del Cliente` As parent
            Inner Join
                `tabMultiple Items` As child
                On child.parenttype = "Producto del Cliente"
                    And child.parentfield = "possible_items"
                    And child.parent = parent.name
            Where
                child.item = {filters["item_code"]!r}
                And parent.cliente = {filters["customer"]!r}
                And parent.name Like {searchstr!r}
        """, as_list=True
    )
    return out
