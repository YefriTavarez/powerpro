# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ArteOriginal(Document):
	def onload(self):
		frappe.msgprint("Hacked! This is a custom message from the ArteOriginal class")
	
	def validate(self):
		frappe.msgprint("This is working like a charm!")
