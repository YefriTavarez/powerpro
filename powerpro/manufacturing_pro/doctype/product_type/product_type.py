# Copyright (c) 2024, Yefri Tavarez and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from frappe.utils import nestedset

class ProductType(Document):
	@frappe.whitelist()
	def get_item_group_root(self):
		return nestedset.get_root_of("Item Group")
