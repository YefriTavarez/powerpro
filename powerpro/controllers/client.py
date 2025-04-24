# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe
from frappe import _

@frappe.whitelist()
def get_producto_del_cliente(texto_busqueda=None, item_group=None):
    conditions = []
    params = []

    if texto_busqueda:
        wildcard = f"%{texto_busqueda}%"
        conditions.append("""(
            item.item_group LIKE %s OR
            item.name LIKE %s OR
            item.description LIKE %s OR
            product.cliente LIKE %s OR
            product.nombre_arte LIKE %s
        )""")
        params.extend([wildcard] * 5)

    if item_group and item_group != "Todos los grupos de artículos":
        conditions.append("""(
            item.custom_item_group_1 = %s OR
            item.custom_item_group_2 = %s OR
            item.custom_item_group_3 = %s OR
            item.custom_item_group_4 = %s OR
            item.custom_item_group_5 = %s
        )""")
        params.extend([item_group] * 5)

    query = """
        SELECT
            item.name,
            item.item_name,
            item.item_group,
            item.description
        FROM
            `tabItem` AS item
        LEFT JOIN
            `tabMultiple Items` AS possible_items
            ON item.name = possible_items.item
        LEFT JOIN
            `tabProducto del Cliente` AS product
            ON
                possible_items.parent = product.name
                AND possible_items.parenttype = 'Producto del Cliente'
                AND possible_items.parentfield = 'possible_items'
        WHERE
            item.disabled = 0
    """

    if conditions:
        query += " AND " + " AND ".join(conditions)

    return frappe.db.sql(query, params, as_dict=True)