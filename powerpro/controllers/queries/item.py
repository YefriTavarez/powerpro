# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_item_by_product_type_query(doctype, txt, searchfield="name", start=0, page_len=20, filters=None):
	"""
	Retrieve item information based on the search text.

	Args:
		doctype (str): The type of document to search within.
		txt (str): The text to search for within item.
		searchfield (str, optional): The field to search within. Defaults to "name".
		start (int, optional): The starting index for the search results. Defaults to 0.
		page_len (int, optional): The number of results to return. Defaults to 20.
		filters (dict, optional): Additional filters to apply to the search. Defaults to None.

	Returns:
		list: A list of item results matching the search criteria.
	"""
	searchstr = "%%"
	if txt:
		searchstr = f"%{txt}%"

	if filters is None:
		filters = {}

	if isinstance(filters, list):
		frappe.msgprint("Please provide a dictionary as filters.", alert=True)
		return []

	if "product_type" not in filters:
		frappe.msgprint("Please provide a product type to search for item.", alert=True)
		return []

	product_type = filters["product_type"]

	out = frappe.db.sql(
		f"""
			Select
				name,
				description
			From
				`tabItem`
			Where
				product_details Like '%"tipo_de_producto": "{product_type}"%'
				And name Like {searchstr!r}
		""", as_list=True
	)
	return out