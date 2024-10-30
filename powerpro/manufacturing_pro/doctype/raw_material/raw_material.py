# Copyright (c) 2024, Yefri Tavarez and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_link_to_form


from .utils import hash_key
from powerpro.utils import (
	round_to_nearest_eighth,
)


class RawMaterial(Document):
	def validate(self):
		# self.round_dimensions()
		self.set_description()
		
		# these two have to be run in this order
		self.set_smart_hash()
		self.validate_existing_smart_hash()

	def get_description(self, as_list=False):
		out = [
			self.base_material,
		]

		if self.base_material == "Paperboard":
			out.append(self.paperboard_type)
			out.append(self.paperboard_caliper)
		elif self.base_material == "Paper":
			out.append(self.paper_type)
			out.append(self.paper_weight)

		if getattr(self, "material_format", None):
			if self.material_format not in ["Roll", "Sheet"]:
				frappe.throw(
					f"Invalid material format: {self.material_format}"
				)

			dimension_map = {
				"Roll": f"{self.roll_width} in",
				"Sheet": f"{self.sheet_width} x {self.sheet_height} in",
			}

			out.append(dimension_map[self.material_format])
		
		if self.gsm:
			out.append(f"{self.gsm} gsm")
		
		if as_list:
			return out

		return ", ".join(out)

	def set_description(self):
		self.description = self.get_description()

	def set_smart_hash(self):
		# self.get_description(as_list=True)
		self.smart_hash = hash_key(
			f"enabled: {self.enabled} - {self.description}"
		)

		if not self.smart_hash:
			frappe.throw(
				f"Unable to generate a hash for this raw material: <br> {self.description}"
			)

	def round_dimensions(self):
		if self.material_format == "Roll":
			self.roll_width = round_to_nearest_eighth(self.roll_width)
		elif self.material_format == "Sheet":
			self.sheet_width = round_to_nearest_eighth(self.sheet_width)
			self.sheet_height = round_to_nearest_eighth(self.sheet_height)

	def validate_existing_smart_hash(self):
		if existing_id := self.get_existing_smart_hash(self.smart_hash):
			link_to_form = get_link_to_form(self.doctype, existing_id, label=self.description)
			frappe.throw(
				f"This raw material already exists as {link_to_form}"
			)

	def get_existing_smart_hash(self, smart_hash: str) -> str:
		doctype = "Raw Material"
		filters = {
			"smart_hash": smart_hash,
			"name": ("!=", self.name),
		}

		return frappe.db.exists(
			doctype, filters
		)

	description: str
	base_material: str
	paperboard_type: str
	paperboard_caliper: str
	paper_type: str
	paper_weight: str
	material_format: str
	roll_width: float
	sheet_width: float
	sheet_height: float
	gsm: int
	smart_hash: str


def on_doctype_update():
	"""Hide base_material from List View"""
	df = frappe.get_doc("DocField", {
		"parent": "Raw Material",
		"fieldname": "base_material",
	})
	
	df.db_set("in_list_view", 0)
