# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt


import frappe


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_items_based_on_original_art(doctype, txt, searchfield="name", start=0, page_len=20, filters=None):
	"""
	Get items based on the original art.

	Args:
		doctype (str): The type of document to search within.
		txt (str): The text to search for within the original art.
		searchfield (str, optional): The field to search within. Defaults to "name".
		start (int, optional): The starting index for the search results. Defaults to 0.
		page_len (int, optional): The number of results to return. Defaults to 20.
		filters (dict, optional): Additional filters to apply to the search. Defaults to None.

	Returns:
		list: A list of items matching the search criteria.
	"""
	searchstr = "%%"
	if txt:
		searchstr = f"%{txt}%"

	conditions = "1 = 1" # default condition
	if txt:
		conditions = f"items.name Like {searchstr!r}" # replace default condition
		conditions += f"Or items.description Like {searchstr!r}"

	if filters is None:
		filters = {}

	if isinstance(filters, list):
		frappe.msgprint("Please provide a dictionary as filters.", alert=True)
		return []

	if "original_art" not in filters:
		frappe.msgprint("Please provide an original art to search for items.", alert=True)
		return []

	out = frappe.db.sql(
		f"""
			Select
				item.name,
				item.description
			From
				`tabItem` As item
			Inner Join
				`tabMultiple Items` As items
				On items.parent = item.name
			Where
				{conditions}
		""", as_list=True
	)
	return out