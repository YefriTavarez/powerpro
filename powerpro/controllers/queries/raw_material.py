# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def raw_material_query(doctype, txt, searchfield, start, page_len, filters):
	"""Return raw materials based on the search criteria"""

	if filters is None:
		filters = {}

	if isinstance(filters, list):
		frappe.throw(
			_("Filters should be a dictionary")
		)


	if product_type := filters.get("product_type"):
		text_conditions = get_txt_conditions(txt)
		return frappe.db.sql(
			f"""
				Select
					material.name,
					material.description
				From
					`tabRaw Material` As material
				Where
					material.name In (
						Select
							child.raw_materials
						From
							`tabRaw Materials` As child
						Where
							child.parenttype = "Product Type"
							And child.parentfield = "raw_materials"
							And child.parent = {product_type!r}
					) {text_conditions} 
			"""
		)
	else:
		if txt:
			filters.update({
				searchfield: ["like", f"'%{txt}%'"]
			})
		frappe.get_all(
			"Raw Material",
			filters=filters,
			fields=["name", "description"],
			as_list=True
		)
	

def get_txt_conditions(txt):
	if txt:
		return f"""
			And material.description like "%{txt}%"
		"""

	return ""
