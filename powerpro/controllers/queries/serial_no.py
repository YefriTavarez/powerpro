# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_serial_no_for_item_query(doctype, txt, searchfield="name", start=0, page_len=20, filters=None):
	"""
	Retrieve serial numbers based on the search text (unused in Conversion Rolls Used).

	Args:
		doctype (str): The type of document to search within.
		txt (str): The text to search for within serial numbers.
		searchfield (str, optional): The field to search within. Defaults to "name".
		start (int, optional): The starting index for the search results. Defaults to 0.
		page_len (int, optional): The number of results to return. Defaults to 20.
		filters (dict, optional): Additional filters to apply to the search. Defaults to None.

	Returns:
		list: A list of serial numbers matching the search criteria.
	"""
	if filters is None:
		filters = {}

	if not filters.get("item_code"):
		frappe.msgprint("Please provide an item code to search for serial numbers.", alert=True)
		return []

	if not filters.get("row_id"):
		frappe.msgprint("Please provide a row ID to search for serial numbers.", alert=True)
		return []

	searchstr = "%%"
	if txt:
		searchstr = f"%{txt}%"

	row_id = filters["row_id"]
	item_code = filters["item_code"]

	if filters.get("skip_list"):
		skip_list = filters["skip_list"]
		if isinstance(skip_list, str):
			skip_list = skip_list.split(",")

		if not isinstance(skip_list, list):
			frappe.msgprint("Please provide a list of serial numbers to skip.", alert=True)
			return []

		skip_list_str = ", ".join([f"{sn!r}" for sn in skip_list])
		skip_condition = f"AND name NOT IN ({skip_list_str})"
	else:
		skip_condition = ""

	out = frappe.db.sql(
		f"""
			SELECT
				name,
				item_code
			FROM
				`tabSerial No`
			WHERE
				name LIKE {searchstr!r}
				And name NOT IN (
					SELECT
						serial_no
					FROM
						`tabConversion Rolls Used`
					WHERE
						name != {row_id!r}
				)
				And item_code = {item_code!r}
				And status = 'Active'
				{skip_condition}
			LIMIT {start}, {page_len}
		""", as_list=True
	)
	return out
