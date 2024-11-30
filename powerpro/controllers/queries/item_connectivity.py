# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


def get_item_connectivity(doctype, txt, searchfield="name", start=0, page_len=20, filters=None):
	"""
	Retrieve item connectivity information based on the search text.

	Args:
		doctype (str): The type of document to search within.
		txt (str): The text to search for within item connectivity.
		searchfield (str, optional): The field to search within. Defaults to "name".
		start (int, optional): The starting index for the search results. Defaults to 0.
		page_len (int, optional): The number of results to return. Defaults to 20.
		filters (dict, optional): Additional filters to apply to the search. Defaults to None.

	Returns:
		list: A list of item connectivity results matching the search criteria.
	"""
	searchstr = "%%"
	if txt:
		searchstr = f"%{txt}%"

	out = frappe.db.sql(
		f"""
			Select
				parent.item_connectivity
			From
				`tabItem Connectivity` As parent
			Inner Join
				`tabItem Name Link` As child
				On child.parenttype = "Item Connectivity"
					And child.parentfield = "item_names"
					And child.parent = parent.name
			Where
				item_connectivity Like {searchstr!r}
		""", as_list=True
	)
	return out