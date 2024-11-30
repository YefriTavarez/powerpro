# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ItemColor(Document):
	def onload(self):
		frappe.msgprint("Hello from the other side!")