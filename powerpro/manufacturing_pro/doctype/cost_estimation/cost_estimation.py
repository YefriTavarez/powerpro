# Copyright (c) 2024, Yefri Tavarez and contributors
# For license information, please see license.txt

from typing import Literal, TYPE_CHECKING

import frappe
from frappe import _

from frappe.model.document import Document

from powerpro.manufacturing_pro.doctype.raw_material.utils import hash_key

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
		smart_hash = self.generate_smart_hash()
		smart_hash_exist = self.does_smart_hash_exist(smart_hash)
		self.set_onload("smart_hash_exist", smart_hash_exist)

		# enable the form_data view in the form
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

		smart_hash = self.generate_smart_hash()

		if name := self.does_smart_hash_exist(smart_hash, as_name=True):
			frappe.throw(
				_("The SKU already exists with the name {name!r}")
				.format(name=name)
			)

		item.update({
			# "item_code": primary_key,
			"item_name": product_type_id,
			# "naming_series": naming_series,
			"description": self.get_product_description(vue_data),
			"is_purchase_item": 0,
			"is_sales_item": 1,
			"is_stock_item": 0,
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
			"product_details": self.data,
			"smart_hash": smart_hash,
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

	@frappe.whitelist()
	def generate_smart_hash(self) -> str:
		"""Generate a smart hash based on the current data"""
		form_data = frappe.parse_json(self.data)

		# ignore_list
		# doc.customer
		# doc.created_on
		# doc.expires_on

		# don't igonore this key
		# doc.raw_material

		# the order in which the product dimension are stored
		# does not impact the hash (but it will if we don't sort them)
		width = form_data.get("ancho_producto", 0)
		height = form_data.get("alto_producto", 0)

		# store the original values first
		form_data["_ancho_producto"] = width
		form_data["_alto_producto"] = height

		# swap the values if the width is greater than the height
		if width > height:
			width, height = height, width

		# store the swapped values in the position of the original values	
		form_data["ancho_producto"] = width
		form_data["alto_producto"] = height

		# ignore this keys from the form_data (self.data)
		ignore_list = {
			"cantidad_montaje",
			"cantidad_de_producto",
			"porcentaje_adicional",
			"margen_de_utilidad",
			"ancho_montaje",
			"alto_montaje",
			"ancho_material",
			"alto_material",
			"tipo_de_empaque",
			"_ancho_producto",
			"_alto_producto",
		}
	
		out = f"{self.raw_material} - "
		for key in sorted(form_data.keys()):
			if key in ignore_list:
				continue

			out += f"{key}: {form_data[key]} - "

		return hash_key(out)

	@frappe.whitelist()
	def does_smart_hash_exist(self, smart_hash: str, as_name: bool=False) -> bool:
		"""Check if the current smart hash already exists"""
		doctype = "Item"
		filters = {
			"smart_hash": smart_hash,
		}

		name = frappe.db.exists(doctype, filters)

		if as_name:
			return name

		return bool(name)

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
