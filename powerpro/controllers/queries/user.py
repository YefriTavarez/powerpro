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


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_active_users_in_department(doctype, txt, searchfield, start, page_len, filters):
	# bring a list of users that are linked to an employee in a specific department (employee must be active)
	# frappe.call({
	# 	method: "powerpro.controllers.project.get_users_in_department",
	# 	args: {
	# 		department: doc.department,
	# 	}
	# });

	searchstr = "%%"
	if txt:
		searchstr = f"%{txt}%"
	if filters is None:
		filters = {}
	if isinstance(filters, list):
		frappe.msgprint("Please provide a dictionary as filters.", alert=True)
		return []
	if "department" not in filters:
		frappe.msgprint("Please provide a department to search for users.", alert=True)
		return []
	out = frappe.db.sql(
		f"""
			Select
				user.name
			From
				`tabUser` As user
			Inner Join
				`tabEmployee` As employee
			On
				user.name = employee.user_id
			Where
				employee.department = {filters["department"]!r}
				And employee.status = 'Active'
				And user.enabled = 1
				And user.name Like {searchstr!r}
			Order By
				user.name
		""", as_list=True
	)

	return out if out else []
