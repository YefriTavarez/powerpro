# Copyright (c) 2024, Yefri Tavarez and contributors
# For license information, please see license.txt

from typing import Literal, TYPE_CHECKING

import frappe
from frappe import _

from frappe.model.document import Document

if TYPE_CHECKING:
	from powerpro.powerpro.manufacturing_pro.doctype.raw_material.raw_material import RawMaterial
	from powerpro.powerpro.manufacturing_pro.doctype.product_type.product_type import ProductType



class CostEstimation(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		created_on: DF.Date
		customer: DF.Link
		data: DF.JSON | None
		expires_on: DF.Date
		naming_series: DF.Literal["COST-EST-"]
		raw_material: DF.Link
	# end: auto-generated types
	def onload(self):
		self.set_onload("debug", False)

	@frappe.whitelist()
	def create_sku(self):
		if not self.data:
			frappe.throw(
				_("No data was provided")
			)
		
		vue_data = frappe.parse_json(self.data)

		if not vue_data:
			frappe.throw(
				_("No data was provided")
			)

		product_type_id = vue_data.get("tipo_de_producto")

		product_type = self.load_product_type(product_type_id)
		
		# let's create the item based on the data
		item = frappe.new_doc("Item")

		item.update({
			# "item_code": primary_key,
			"item_name": product_type_id,
			# "naming_series": naming_series,
			"description": self.get_product_description(vue_data),
			"is_purchase_item": 0,
			"is_sales_item": 1,
			"is_stock_item": 1,
			"custom_item_group_1": product_type.item_group_1,
			"custom_item_group_2": product_type.item_group_2,
			"custom_item_group_3": product_type.item_group_3,
			"custom_item_group_4": product_type.item_group_4,
			"custom_item_group_5": product_type.item_group_5,
			"item_group": self.get_final_item_group(product_type),
			"allow_alternative_item": 1,
			"default_material_request_type": "Purchase",
			"include_item_in_manufacturing": 1,
			"item_type": "Bienes",
			"reference_type": self.doctype,
			"reference_name": self.name,
			"stock_uom": self.get_default_product_uom(),
			"valuation_method": "FIFO",
		})

		item.insert()

		return item.name

	def get_product_description(self, data):
		settings = frappe.get_single("Power-Pro Settings")

		if not settings.description_template_for_product:
			frappe.throw(
				_("'Description Template for Product' is not set in the Power-Pro Settings")
			)

		context = dict(
			mat=self.get_material_as_dict(self.raw_material),
			est=frappe._dict(data),
			doc=self.as_dict(),
			frappe=frappe._dict(
				utils=frappe.utils
			)
		)

		return frappe.render_template(
			settings.description_template_for_product, context
		)		

	def get_default_product_uom(self):
		settings = frappe.get_single("Power-Pro Settings")
		if not settings.product_uom:
			frappe.throw(
				_("Product UOM is not set in the Power-Pro Settings")
			)
		
		return settings.product_uom

	def get_material_as_dict(self, material: str) -> dict:
		"""Get the material based on the given material ID"""
		doctype = "Raw Material"

		if not material:
			frappe.throw(
				_("Raw Material ID is required")
			)

		if not frappe.db.exists(doctype, material):
			frappe.throw(
				_("Raw Material '{material}' not found")
				.format(material=material)
			)

		material: "RawMaterial" = frappe.get_doc(doctype, material)

		return material.as_dict()

	def load_product_type(self, product_type_id: str) -> "ProductType":
		"""Load the product type based on the given product type ID"""
		doctype = "Product Type"

		if not product_type_id:
			frappe.throw(
				_("Product Type ID is required")
			)

		if not frappe.db.exists(doctype, product_type_id):
			frappe.throw(
				_("Product Type '{product_type_id}' not found")
				.format(product_type_id=product_type_id)
			)

		return frappe.get_doc(doctype, product_type_id)

	def get_final_item_group(self, product_type: "ProductType") -> str:
		"""Get the final item group based on the given product type"""
		return product_type.item_group_5 \
			or product_type.item_group_4 \
			or product_type.item_group_3 \
			or product_type.item_group_2 \
			or product_type.item_group_1
