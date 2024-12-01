# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_item_model(doctype, txt, searchfield="name", start=0, page_len=20, filters=None):
	"""
	Retrieve item model information based on the search text.

	Args:
		doctype (str): The type of document to search within.
		txt (str): The text to search for within item model.
		searchfield (str, optional): The field to search within. Defaults to "name".
		start (int, optional): The starting index for the search results. Defaults to 0.
		page_len (int, optional): The number of results to return. Defaults to 20.
		filters (dict, optional): Additional filters to apply to the search. Defaults to None.

	Returns:
		list: A list of item model results matching the search criteria.
	"""
	searchstr = "%%"
	if txt:
		searchstr = f"%{txt}%"

	if filters is None:
		filters = {}

	if isinstance(filters, list):
		frappe.msgprint("Please provide a dictionary as filters.", alert=True)
		return []

	if "item_name" not in filters:
		frappe.msgprint("Please provide an item name to search for item model.", alert=True)
		return []

	out = frappe.db.sql(
		f"""
			Select
				parent.item_model
			From
				`tabItem Model` As parent
			Inner Join
				`tabItem Name Link` As child
				On child.parenttype = "Item Model"
					And child.parentfield = "item_names"
					And child.parent = parent.name
			Where
				child.item_name = {filters["item_name"]!r}
				And item_model Like {searchstr!r}
		""", as_list=True
	)
	return out