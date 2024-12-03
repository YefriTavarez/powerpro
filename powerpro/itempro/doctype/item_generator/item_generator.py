# Copyright (c) 2024, Yefri Tavarez and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_link_to_form

from frappe.model.document import Document

from powerpro.manufacturing_pro.doctype.raw_material.utils import hash_key

class ItemGenerator(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		autonomy: DF.Int
		autonomy_uom: DF.Link | None
		brand: DF.Link | None
		capacity: DF.Float
		capacity_uom: DF.Link | None
		capcidad_udm: DF.Link | None
		color: DF.Link | None
		conectividad: DF.Link | None
		current: DF.Link | None
		custom: DF.Literal["", "Bordado", "Grabado", "Impreso"]
		depth: DF.Float
		depth_uom: DF.Link | None
		description: DF.LongText | None
		diameter: DF.Float
		diameter_uom: DF.Link | None
		finish: DF.Link | None
		flavour: DF.Link | None
		frequency: DF.Literal["", "50Hz", "60Hz"]
		garantía: DF.Int
		garantía_udm: DF.Link | None
		gauge: DF.Float
		gauge_uom: DF.Link | None
		height: DF.Float
		height_uom: DF.Link | None
		item: DF.Link | None
		material: DF.Link | None
		model: DF.Link | None
		packaging: DF.Link | None
		pcs: DF.Int
		phase: DF.Link | None
		presentation: DF.Float
		presentation_uom: DF.Link | None
		production_capacity: DF.Int
		shape: DF.Link | None
		size: DF.Link | None
		smart_hash: DF.SmallText | None
		spec1: DF.Link | None
		spec2: DF.Link | None
		use: DF.Link | None
		voltage: DF.Link | None
		weight: DF.Float
		weight_uom: DF.Link | None
		width: DF.Float
		width_uom: DF.Link | None
		year: DF.Literal["", "1970", "1971", "1972", "1973", "1974", "1975", "1976", "1977", "1978", "1979", "1980", "1981", "1982", "1983", "1984", "1985", "1986", "1987", "1988", "1989", "1990", "1991", "1992", "1993", "1994", "1995", "1996", "1997", "1998", "1999", "2000", "2001", "2002", "2003", "2004", "2005", "2006", "2007", "2008", "2009", "2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026"]
	# end: auto-generated types
	def validate(self):
		self.self_validate_for_uniqueness()

	def before_save(self):
		self.render_description()

	def render_description(self):
		item_name = frappe.get_doc("Item Name", self.item)

		if template := item_name.item_description_template:
			self.description = frappe.render_template(template, self.as_dict())
		else:
			frappe.throw("No se especificó el valor para el campo 'Plantilla para la Descripción' en el doctype Nombre de Producto")

	def on_update(self):
		self.enqueue_doc(
			method="update_existing_items",
			doctype=self.doctype,
			name=self.name,
			enqueue_after_commit=True,
			queue="default",
		)

	def self_validate_for_uniqueness(self):
		self.self_generate_smart_hash()

		if not self.smart_hash:
			frappe.throw("No se pudo generar el hash inteligente para este registro")
		
		filters = {
			"smart_hash": self.smart_hash,
			"name": ["!=", self.name],
		}

		if name := frappe.db.exists(self.doctype, filters):
			# let's be cautious about the run of this function 'render_description'
			# because it already runs in the 'before_save' method. Which means it will
			# run twice (once after this call). We need the description here to display
			# it in the error message.
			self.render_description()

			link_to_form = get_link_to_form(self.doctype, name, label=self.description)
			frappe.throw(
				f"fYa existe un Item Generator con el mismo hash inteligente: {link_to_form}"
			)

	def self_generate_smart_hash(self):
		# We need to know what fields are being displayed for this record.
		# This is tied to the selected Item Name, so we need to get it first.
		item_name = frappe.get_doc("Item Name", self.item)

		# Item Name has a child-table that can be accessed via the "fields" property
		# but first, let's clean the fields that are not being displayed in the Item Name
		# so we can avoid unnecessary iterations.
		for field in item_name.fields:
			if field.item_show_field:
				continue

			self.set(field.item_field_name, None)

		values = list()
		# Now we can iterate over the fields that are being displayed
		for field in item_name.fields:
			if not field.item_show_field:
				continue

			value = self.get(field.item_field_name)

			values.append(f"{field.item_field_name} = '{value}'")
		
		rawvals = " ".join(values)
		self.smart_hash = hash_key(rawvals)

	def update_existing_items(self):
		doctype = "Item"
		filters = {
			"reference_type": self.doctype,
			"reference_name": self.name,
		}

		for item in frappe.get_all(doctype, filters):
			doc = frappe.get_doc(doctype, item.name)
			doc.description = self.description
			doc.save()
