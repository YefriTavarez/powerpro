# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import nestedset

CATEGORY_RANGES = {
    "Artículos": (1000, 3999),
    "Productos": (4000, 7999),
    "Servicios": (9000, 9999),
}

def after_insert(doc, method=None):
	_set_item_group_number(doc)


def on_update(doc, method=None):
	queue_update_of_items(doc)


def _set_item_group_number(doc):
	"""Set the item_group_number field to the next number in the sequence"""
	doc.db_set("item_group_number", generate_item_group_number(doc))

def generate_item_group_number(doc):
    """Generate a unique 4-digit item group number based on root category."""
    root_category = get_root_category(doc)
    if root_category not in CATEGORY_RANGES:
        frappe.throw(f"No range defined for root category: {root_category}")

    start, end = CATEGORY_RANGES[root_category]
    used_numbers = frappe.db.get_all(
        "Item Group",
        filters={"item_group_number": ["between", [start, end]]},
        pluck="item_group_number",
    )

    used_numbers = set(int(num) for num in used_numbers if num.isdigit())

    for number in range(start, end + 1):
        if number not in used_numbers:
            return f"{number:04d}"

    frappe.throw(f"No available numbers in range for root category: {root_category}")

def get_root_category(doc):
    """Traverse up the tree to find the root category."""
    while doc.parent_item_group and doc.parent_item_group != "Todos los grupos de artículos":
        doc = frappe.get_doc("Item Group", doc.parent_item_group)
    return doc.name

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
