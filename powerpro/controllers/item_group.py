# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe
from frappe.utils import nestedset

def on_update(doc, method=None):
	queue_update_of_items(doc)


def queue_update_of_items(doc):
	"""Will update the Item Tax in all Items related to this Item Group"""
	frappe.enqueue(
		method="powerpro.controllers.item_group.update_item_tax_of_items",
		queue="long",
		timeout=1500,
		item_group_id=doc.name,
		enqueue_after_commit=True,
	)


@frappe.whitelist()
def update_item_tax_of_items(item_group_id):
	"""Will update the Item Tax in all Items related to this Item Group"""
	doctype = "Item Group"
	
	out = [item_group_id] + nestedset.get_descendants_of(
		doctype, item_group_id
	)

	item_group = get_item_group(item_group_id)

	for item_id in frappe.get_all("Item", filters={"item_group": ("in", out)}, pluck="name"):
		item = frappe.get_doc("Item", item_id)
		item.taxes = []

		for tax in item_group.taxes:
			item.append("taxes", frappe.copy_doc(tax))

		item.save(ignore_permissions=True)
	

def get_item_group(item_group_id):
	return frappe.get_doc("Item Group", item_group_id)
