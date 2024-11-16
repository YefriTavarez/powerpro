# Copyright (c) 2024, Yefri Tavarez and contributors
# For license information, please see license.txt

import frappe

from frappe import _
from frappe.model.document import Document
from frappe.utils import get_link_to_form


from .utils import hash_key
from powerpro.utils import (
	round_to_nearest_eighth,
)


class RawMaterial(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		base_material: DF.Literal["", "Paperboard", "Paper", "Adhesive Paper", "Adhesive Vinyl"]
		description: DF.SmallText | None
		enabled: DF.Check
		paper_type: DF.Literal["", "Bond", "Couch\u00e9"]
		paper_weight: DF.Literal["", "20", "24", "60", "80", "100", "120"]
		paperboard_caliper: DF.Literal["", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "22", "24", "26", "28"]
		paperboard_type: DF.Literal["", "Uncoated Kraft Multi-layer", "White Back Multi-layer", "Kraft Back Multi-layer", "Recycled Grey Back", "Recycled Kraft Back", "Uncoated Solid Kraft", "White Back Solid", "Kraft Back Solid"]
		smart_hash: DF.Data | None
	# end: auto-generated types
	def validate(self):
		# self.round_dimensions()
		self.set_description()
		
		# these two have to be run in this order
		self.set_smart_hash()
		self.validate_existing_smart_hash()

	def get_description(self, as_list=False):
		out = [
			_(self.base_material),
		]

		if self.base_material == "Paperboard":
			out.append(
				_(self.paperboard_type)
			)
			out.append(
				_(self.paperboard_caliper)
			)
		elif self.base_material == "Paper":
			out.append(
				_(self.paper_type)
			)
			out.append(
				_(self.paper_weight)
			)

		if getattr(self, "material_format", None):
			if self.material_format not in ["Roll", "Sheet"]:
				frappe.throw(
					f"Invalid material format: {self.material_format}"
				)

			if self.material_format == "Roll":
				if not hasattr(self, "roll_width"):
					raise ValueError("Roll Width is required for Roll format")

			elif self.material_format == "Sheet":
				if not hasattr(self, "sheet_width"):
					raise ValueError("Sheet Width is required for Sheet format")

				if hasattr(self, "sheet_height"):
					raise ValueError("Sheet Height is required for Sheet format")

			dimension_map = {
				"Roll": f"{self.roll_width} in",
				"Sheet": f"{self.sheet_width} x {self.sheet_height} in",
			}

			out.append(
				_(dimension_map[self.material_format])
			)

		if getattr(self, "gsm", None):
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
				f"{_('Unable to generate a hash for this raw material')}: <br> {self.description}"
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
				f"{_('This raw material already exists as')} {link_to_form}"
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


def on_doctype_update():
	"""Hide base_material from List View"""
	df = frappe.get_doc("DocField", {
		"parent": "Raw Material",
		"fieldname": "base_material",
	})
	
	df.db_set("in_list_view", 0)
