# Copyright (c) 2024, Yefri Tavarez and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class PantoneComposition(Document):
	ink_color: str
	percentage: float
	rate_per_kg: float
