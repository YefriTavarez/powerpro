# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def get_power_pro_settings(fields=None):
	if isinstance(fields, str):
		if fields.startswith("["):
			fields = frappe.parse_json(fields)
		else:
			fields = [fields]

	if not isinstance(fields, list):
		fields = None

	settings = frappe.get_single("Power-Pro Settings")

	_fields = [
		"root_item_group_for_raw_materials",
		"product_uom",
		"material_roll_uom",
		"material_sheet_uom",
		"description_template_for_raw_material",
		"description_template_for_product",
		"min_margin",
		"max_margin",
		"cyan_color",
		"magenta_color",
		"yellow_color",
		"key_color",
	]

	if fields:
		# validate fields
		_fields = list(set(fields) & set(_fields))

	if not fields:
		fields = _fields

	return {field: settings.get(field) for field in fields}