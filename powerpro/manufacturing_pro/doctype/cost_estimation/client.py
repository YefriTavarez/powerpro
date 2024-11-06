# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import functools
from typing import List, Dict

import frappe


@frappe.whitelist()
def get_product_type_details(product_type: str) -> List[Dict]:
	if "operation_type" not in get_table_columns("Operation"):
		frappe.throw("The doctype Operation has not been fully configured yet")

	return frappe.db.sql(f"""
		Select
			operation.name As operation,
			operation.operation_type As operation_type
		From
			`tabOperation` As operation
		Inner Join
			`tabProduct Operations` As operations
			On
				operation.name = operations.operation
		Where
			operations.parent = {product_type!r}
			And operations.parenttype = "Product Type"
			And operations.parentfield = "product_operations"
	""", as_dict=True)


@functools.lru_cache()
def get_table_columns(doctype: str) -> List[str]:
	return frappe.db.get_table_columns(doctype)
