# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def get_workstation(doctype, txt, searchfield="name", start=0, page_len=20, filters=None):
	"""
	Retrieve workstation information based on the search text.

	Args:
		doctype (str): The type of document to search within.
		txt (str): The text to search for within workstation.
		searchfield (str, optional): The field to search within. Defaults to "name".
		start (int, optional): The starting index for the search results. Defaults to 0.
		page_len (int, optional): The number of results to return. Defaults to 20.
		filters (dict, optional): Additional filters to apply to the search. Defaults to None.

	Returns:
		list: A list of workstation results matching the search criteria.
	"""
	searchstr = "%%"
	if txt:
		searchstr = f"%{txt}%"

	if filters is None:
		filters = {}

	if isinstance(filters, list):
		frappe.msgprint("Please provide a dictionary as filters.", alert=True)
		return []

	if "operation_type" not in filters:
		frappe.msgprint("Please provide an 'Operation Type' to search for operation.", alert=True)
		return []

	additionals = ""
	if searchstr != "%%":
		additionals = f"And workstation.name Like {searchstr!r}"

	out = frappe.db.sql(
		f"""
			Select
				workstation.name
			From
				`tabOperation Type` As operation_type
			Inner Join
				`tabWorkstation` As workstation
				On workstation.workstation_type = operation_type.workstation_type
			Where
				operation_type.name = {filters["operation_type"]!r}
				{additionals}
		""", as_list=True
	)
	return out