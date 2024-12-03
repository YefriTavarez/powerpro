# Copyright (c) 2024, Yefri Tavarez and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class ItemModel(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from powerpro.itempro.doctype.item_brands.item_brands import ItemBrands
		from powerpro.itempro.doctype.item_name_link.item_name_link import ItemNameLink

		item_brands: DF.TableMultiSelect[ItemBrands]
		item_model: DF.Data | None
		item_names: DF.Table[ItemNameLink]
	# end: auto-generated types
	pass
