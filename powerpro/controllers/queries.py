# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def raw_material_query(doctype, txt, searchfield, start, page_len, filters):
	if filters is None:
		filters = {}

	if isinstance(filters, list):
		frappe.throw(
			"Filters must be a dictionary"
		)

	if product_type := filters.get("product_type"):
		del filters["product_type"]

		filters.update({
			"parent": product_type,
		})

	if txt:
		filters.update({
			"raw_materials": ["like", f"%{txt}%"],
		})

	materials_map = get_materials_map()
	return [(d[0], materials_map[d[0]]) for d in frappe.get_all(
		"Raw Materials",
		filters=filters,
		fields=["raw_materials"],
		as_list=True,
	)]


def get_materials_map() -> dict:
	doctype = "Raw Material"
	filters = {
		
	}

	fields = [
		"name",
		"description",
	]

	return dict(
		frappe.get_all(doctype, filters, fields, as_list=True)
	)