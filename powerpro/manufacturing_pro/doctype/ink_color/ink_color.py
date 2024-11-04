# Copyright (c) 2024, Yefri Tavarez and contributors
# For license information, please see license.txt

from typing import List, Literal, TYPE_CHECKING

import frappe
from frappe.model.document import Document

if TYPE_CHECKING:
	from powerpro.manufacturing_pro.doctype.pantone_composition import pantone_composition

class InkColor(Document):
	def validate(self):
		self.ensure_100_percent_pantone_composition()
		self.clear_pantone_composition_if_applies()
		self.clear_pantone_type_if_applies()

	def on_update(self):
		self.update_rate_per_kg_if_applies()

	def clear_pantone_type_if_applies(self):
		if self.ink_type != "Pantone":
			self.pantone_type = None

	def clear_pantone_composition_if_applies(self):
		if self.ink_type != "Pantone" \
			or self.pantone_type != "Formula":
			self.pantone_composition = list()

	def update_rate_per_kg_if_applies(self):
		# if the rate_per_kg is based on formula, let's then calculate it
		# here.

	def ensure_100_percent_pantone_composition(self):
		if self.ink_type == "Pantone" \
			and self.pantone_type == "Formula":
			self.validate_pantone_composition()

	def validate_pantone_composition(self):
		total_percentage = sum([
			item.get("percentage", 0)
			for item in self.pantone_composition
		])

		if total_percentage != 100:
			frappe.throw("The total percentage of the Pantone composition must be 100")


	ink_name: str
	ink_type: Literal["Pantone", "Process"]
	pantone_type: Literal["Base", "Formula", "Metallic"]
	hexadecimal_color: str
	rate_per_kg: float
	currency: str
	pantone_composition: List["pantone_composition.PantoneComposition"]
