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


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_sales_order_items(doctype, txt, searchfield, start, page_len, filters):
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
	if not filters:
		frappe.msgprint("Please provide a sales order to search for items.", alert=True)
		return []

	sales_order = filters.get("sales_order")

	if not txt:
		txt = "%%"
	else:
		if "%" not in txt:
			txt = f"%{txt}%"

	if not sales_order:
		frappe.msgprint("Please provide a sales order to search for items.", alert=True)
		return []

	out = frappe.db.sql(
		f"""
			Select
				item_code,
				item_name,
				description
			From
				`tabSales Order Item`
			Where
				parent = {sales_order!r}
				And (
					item_code Like {txt!r}
					Or item_name Like {txt!r}
					Or description Like {txt!r}
				)
			Order By
				item_code Asc
			Limit
				{start}, {page_len}
		""", as_list=True
	)
	return out


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_items_with_active_serial_no(doctype, txt, searchfield, start, page_len, filters):
	# example filters: filters = {
	# 	reference_name: doc.raw_material || "N/A",
	# 	raw_material_type: "Roll",
	# 	roll_width: [">=", Math.min(doc.sheet_width, doc.sheet_height) ],
	# }

	if not filters:
		filters = {}

	if not filters.get("reference_name"):
		frappe.msgprint("Por favor, proporcione un nombre de referencia para buscar los artículos.", alert=True)
		return []

	if not filters.get("raw_material_type"):
		frappe.msgprint("Por favor, proporcione un tipo de materia prima para buscar los artículos.", alert=True)
		return []
	
	conditions = ["i.disabled = 0"]

	values = {}

	# Filter by reference_name
	if filters.get("reference_name"):
		conditions.append("i.reference_name = %(reference_name)s")
		values["reference_name"] = filters["reference_name"]

	# Filter by raw_material_type
	if filters.get("raw_material_type"):
		conditions.append("i.raw_material_type = %(raw_material_type)s")
		values["raw_material_type"] = filters["raw_material_type"]

	# Filter by roll_width (can be a value or a list like [operator, value])
	if filters.get("roll_width"):
		roll_width = filters["roll_width"]
		if isinstance(roll_width, list) and len(roll_width) == 2:
			op, val = roll_width
			if op in [">", ">=", "<", "<=", "=", "!="]:
				conditions.append(f"i.roll_width {op} %(roll_width)s")
				values["roll_width"] = val
		else:
			conditions.append("i.roll_width = %(roll_width)s")
			values["roll_width"] = roll_width

	# Search text
	if txt:
		search_pattern = f"%{txt}%"
		conditions.append("(i.name LIKE %(txt)s OR i.item_name LIKE %(txt)s OR i.description LIKE %(txt)s)")
		values["txt"] = search_pattern

	where_clause = " AND ".join(conditions)

	query = f"""
		SELECT
			i.name,
			i.description
		FROM
			`tabItem` i
		WHERE
			{where_clause}
			And i.name in (
				Select sn.item_code 
				From `tabSerial No`  as sn
				Where sn.status = 'Active'
			)
		ORDER BY
			i.name ASC
		LIMIT {start}, {page_len}
	"""

	return frappe.db.sql(query, values, as_list=True)
