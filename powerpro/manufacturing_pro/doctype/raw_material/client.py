# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

from typing import Literal, TYPE_CHECKING

import frappe
from frappe.utils import get_link_to_form

from powerpro.utils import (
	round_to_nearest_eighth,
	generate_material_primary_key,
)

if TYPE_CHECKING:
	from .raw_material import RawMaterial


@frappe.whitelist()
def create_material_sku(
	material_id: str,
	material_format: Literal["Roll", "Sheet"],
	item_group_1: str,
	item_group_2: str,
	item_group_3: str = None,
	item_group_4: str = None,
	item_group_5: str = None,
	roll_width: float = 0.0,
	sheet_width: float = 0.0,
	sheet_height: float = 0.0,
	gsm: int = 0,
):
	"""Create a new SKU based on the given parameters"""
	# validate material format
	if not material_format:
		frappe.throw("Material format is required")
	
	if material_format not in ("Roll", "Sheet"):
		frappe.throw(
			f"Invalid material format: {material_format}"
			"Should be either 'Roll' or 'Sheet'"
		)


	# update material with new dimensions to get a more accurate description
	material = get_material(material_id)
	material.update({
		"material_format": material_format,
		"roll_width": round_to_nearest_eighth(roll_width),
		"sheet_width": round_to_nearest_eighth(sheet_width),
		"sheet_height": round_to_nearest_eighth(sheet_height),
		"gsm": gsm,
	})

	description = material.get_description()

	# validate an equivalent Item does not exists already in the system.
	if name := frappe.db.exists("Item", {
		"description": description,
	}):
		link_to_form = get_link_to_form("Item", name, description)
		frappe.throw(
			f"This Item or SKU already exists as {link_to_form}"
		)

	# generate the new item code and naming series
	naming_series, primary_key = generate_material_primary_key(
		material.base_material, include_naming_serie=True
	)

	# create and update the new item
	item = frappe.new_doc("Item")

	item.update({
		"item_code": primary_key,
		"item_name": description or material.description,
		"naming_series": naming_series,
		"description": description,
		"is_purchase_item": 1,
		"is_sales_item": 0,
		"is_stock_item": 1,
		"item_group_1": item_group_1,
		"item_group_2": item_group_2,
		"item_group_3": item_group_3,
		"item_group_4": item_group_4,
		"item_group_5": item_group_5,
		"item_group": item_group_5 or item_group_4 or item_group_3 or item_group_2 or item_group_1,
		"allow_alternative_item": 1,
		"default_material_request_type": "Purchase",
		"include_item_in_manufacturing": 1,
		"item_type": "Bienes",
		"reference_type": material.doctype,
		"reference_name": material.name,
		"stock_uom": "ud(s)" if material_format == "Sheet" else "Tonelada",
		"valuation_method": "FIFO",
	})

	item.__newname = primary_key

	item.flags.ignore_mandatory = True
	item.flags.ignore_links = True
	item.save()
	
	return item.name


def get_material(name: str) -> "RawMaterial":
	"""Get the material based on the given material ID"""
	doctype = "Raw Material"

	if not name:
		frappe.throw("Material ID is required")

	if not frappe.db.exists(doctype, name):
		frappe.throw(f"Material {name} not found")

	return frappe.get_doc(doctype, name)
