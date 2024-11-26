# Copyright (c) 2024, Yefri Tavarez and contributors
# For license information, please see license.txt

from typing import Literal, TYPE_CHECKING

import frappe
from frappe import _
from frappe.utils import cint

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
		product_type: DF.Link
		raw_material: DF.Link
	# end: auto-generated types
	def onload(self):
		smart_hash = self.generate_smart_hash()
		if item_id := self.does_smart_hash_exist(smart_hash, as_name=True):
			self.set_onload("item_id", item_id)
			self.set_onload("smart_hash_exist", True)
		else:
			self.set_onload("smart_hash_exist", False)

		# enable the form_data view in the form
		self.set_onload("debug", False)

	def on_update(self):
		form_data = frappe.parse_json(self.data)
		self.clean_up_data(form_data)
		self.sort_colors(form_data)

		self.db_set("data", frappe.as_json(form_data))

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


		self.clean_up_data(form_data)
		self.sort_colors(form_data)
		self.sort_product_dimension(form_data)
		self.sort_utility_dimension(form_data)
		self.sort_special_effects_dimension(form_data)

		# ignore this keys from the form_data (self.data)
		ignore_list = {
			"cantidad_montaje",
			"cantidad_de_producto",
			"porcentaje_adicional",
			"margen_de_utilidad",
			"troquel_en_inventario",
			"ancho_montaje",
			"alto_montaje",
			"ancho_material",
			"alto_material",
			"tipo_de_empaque",
			"ancho_producto",
			"alto_producto",
			"tinta_seleccionada_tiro_1",
			"tinta_seleccionada_tiro_2",
			"tinta_seleccionada_tiro_3",
			"tinta_seleccionada_tiro_4",
			"tinta_seleccionada_tiro_5",
			"tinta_seleccionada_tiro_6",
			"tinta_seleccionada_tiro_7",
			"tinta_seleccionada_tiro_8",
			"tinta_seleccionada_retiro_1",
			"tinta_seleccionada_retiro_2",
			"tinta_seleccionada_retiro_3",
			"tinta_seleccionada_retiro_4",
			"tinta_seleccionada_retiro_5",
			"tinta_seleccionada_retiro_6",
			"tinta_seleccionada_retiro_7",
			"tinta_seleccionada_retiro_8",
			"hex_tinta_seleccionada_tiro_1",
			"hex_tinta_seleccionada_tiro_2",
			"hex_tinta_seleccionada_tiro_3",
			"hex_tinta_seleccionada_tiro_4",
			"hex_tinta_seleccionada_tiro_5",
			"hex_tinta_seleccionada_tiro_6",
			"hex_tinta_seleccionada_tiro_7",
			"hex_tinta_seleccionada_tiro_8",
			"hex_tinta_seleccionada_retiro_1",
			"hex_tinta_seleccionada_retiro_2",
			"hex_tinta_seleccionada_retiro_3",
			"hex_tinta_seleccionada_retiro_4",
			"hex_tinta_seleccionada_retiro_5",
			"hex_tinta_seleccionada_retiro_6",
			"hex_tinta_seleccionada_retiro_7",
			"hex_tinta_seleccionada_retiro_8",
			"cinta_doble_cara_ancho_punto",
			"cinta_doble_cara_alto_punto",
			"ancho_elemento_relieve_1",
			"ancho_elemento_relieve_2",
			"ancho_elemento_relieve_3",
			"ancho_elemento_relieve_4",
			"ancho_elemento_relieve_5",
			"alto_elemento_relieve_1",
			"alto_elemento_relieve_2",
			"alto_elemento_relieve_3",
			"alto_elemento_relieve_4",
			"alto_elemento_relieve_5",
		}
	
		out = f"{self.raw_material} - "
		for key in sorted(form_data.keys()):
			if key in ignore_list:
				continue

			out += f"{key}: {form_data[key]} - "

		return hash_key(out)
	# delete sub-options if primary checkbox is not checked

	@staticmethod
	def clean_up_data(form_data):
		if not form_data.incluye_barnizado:
			if "tipo_barnizado" in form_data:
				del form_data["tipo_barnizado"]

		if not form_data.incluye_laminado:
			if "tipo_laminado" in form_data:
				del form_data["tipo_laminado"]

		if not form_data.incluye_relieve:
			if "tipo_de_relieve" in form_data:
				del form_data["tipo_de_relieve"]

			if "tipo_de_material_relieve" in form_data and form_data.tipo_de_relieve != "Estampado":
				del form_data["tipo_de_material_relieve"]

			if "cantidad_de_elementos_en_relieve" in form_data:
				del form_data["cantidad_de_elementos_en_relieve"]

				for index in range(1, 6):
					if f"ancho_elemento_relieve_{index}" in form_data:
						del form_data[f"ancho_elemento_relieve_{index}"]

				for index in range(1, 6):
					if f"alto_elemento_relieve_{index}" in form_data:
						del form_data[f"alto_elemento_relieve_{index}"]

		if not form_data.incluye_troquelado:
			if "troquel_en_inventario" in form_data:
				del form_data["troquel_en_inventario"]

		if not form_data.incluye_utilidad or form_data.tipo_utilidad != "Cinta Doble Cara":
			if "tipo_utilidad" in form_data:
				del form_data["tipo_utilidad"]
			if "cinta_doble_cara_cantidad_de_puntos" in form_data:
				del form_data["cinta_doble_cara_cantidad_de_puntos"]
			if "cinta_doble_cara_ancho_punto" in form_data:
				del form_data["cinta_doble_cara_ancho_punto"]
			if "cinta_doble_cara_alto_punto" in form_data:
				del form_data["cinta_doble_cara_alto_punto"]

		if not form_data.incluye_pegado:
			if "tipo_pegado" in form_data:
				del form_data["tipo_pegado"]

	@staticmethod
	def sort_colors(form_data):
		front_colors = []
		back_colors = []

		# tinta_seleccionada_tiro_[0-8]
		front_color_prefix = "tinta_seleccionada_tiro_{index}"

		front_colors_qty = cint(
			form_data.get("cantidad_de_tintas_tiro")
		)

		# tinta_seleccionada_retiro_[0-8]
		back_color_prefix = "tinta_seleccionada_retiro_{index}"

		back_colors_qty = cint(
			form_data.get("cantidad_de_tintas_retiro")
		)

		for index in range(1, 9):
			fieldname = front_color_prefix.format(index=index)
			if index <= front_colors_qty:
				color_code = form_data.get(fieldname)
				front_colors.append(
					str(color_code)
				)
				continue

			if fieldname in form_data:
				del form_data[fieldname]

			if f"hex_{fieldname}" in form_data:
				del form_data[f"hex_{fieldname}"]

		for index in range(1, 9):
			fieldname = back_color_prefix.format(index=index)
			if index <= back_colors_qty:
				color_code = form_data.get(fieldname)
				back_colors.append(
					str(color_code)
				)
				continue

			if fieldname in form_data:
				del form_data[fieldname]

			if f"hex_{fieldname}" in form_data:
				del form_data[f"hex_{fieldname}"]

		form_data["front_colors"] = ",".join(
			sorted(front_colors)
		)

		form_data["back_colors"] = ",".join(
			sorted(back_colors)
		)

	@staticmethod
	def sort_utility_dimension(form_data):
		# we need to make sure that no matter the order in which the dimensions are stored
		# the hash is always the same
		# we will sort the dimensions based on the width and height

		width = form_data.get("cinta_doble_cara_ancho_punto", 0)
		height = form_data.get("cinta_doble_cara_alto_punto", 0)

		# swap the values if the width is greater than the height
		if width > height:
			width, height = height, width
		
		form_data["cinta_doble_cara_dimension_punto"] = f"{width}x{height}"

	@staticmethod
	def sort_product_dimension(form_data):
		# the order in which the product dimension are stored
		# does not impact the hash (but it will if we don't sort them)
		width = form_data.get("ancho_producto", 0)
		height = form_data.get("alto_producto", 0)

		# swap the values if the width is greater than the height
		if width > height:
			width, height = height, width

		form_data["dimension_producto"] = f"{width}x{height}"

	@staticmethod
	def sort_special_effects_dimension(form_data):
		# ancho_elemento_relieve_[0-5]
		# alto_elemento_relieve_[0-5]

		dimensions = list()

		for index in range(1, 6):
			width = form_data.get(f"ancho_elemento_relieve_{index}", 0)
			height = form_data.get(f"alto_elemento_relieve_{index}", 0)

			# swap the values if the width is greater than the height
			if width > height:
				width, height = height, width

			dimensions.append(
				f"{width}x{height}"
			)
		
		form_data["dimension_elemento_relieve"] = ",".join(
			sorted(dimensions)
		)

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
