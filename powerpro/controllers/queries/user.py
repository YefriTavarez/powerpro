# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_user_list_for_customer(doctype, txt, searchfield, start, page_len, filters):
	"""
	Retrieve a list of users associated with a specific customer from the `tabPortal User` table.
	Args:
		doctype (str): The DocType to search within (not used in the function).
		txt (str): The text to search for in the user field.
		searchfield (str): The field to search within (not used in the function).
		start (int): The starting index of the search results (not used in the function).
		page_len (int): The number of results to return (not used in the function).
		filters (dict): A dictionary containing filter criteria. Must include a "customer" key.
	Returns:
		list: A list of users matching the search criteria, or an empty list if no users are found or if filters are invalid.
	"""
	
	searchstr = "%%"
	if txt:
		searchstr = f"%{txt}%"

	if filters is None:
		filters = {}

	if isinstance(filters, list):
		frappe.msgprint("Please provide a dictionary as filters.", alert=True)
		return []

	if "customer" not in filters:
		frappe.msgprint("Please provide a customer to search for users.", alert=True)
		return []

	out = frappe.db.sql(
		f"""
			Select
				user
			From
				`tabPortal User`
			Where
				parent = {filters["customer"]!r}
				And user Like {searchstr!r}
		""", as_list=True
	)
	return out
