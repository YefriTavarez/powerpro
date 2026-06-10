# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import re

import frappe
from frappe.utils import cint


ITEM_GROUP_FIELDS = (
	"custom_item_group_1",
	"custom_item_group_2",
	"custom_item_group_3",
	"custom_item_group_4",
	"custom_item_group_5",
)


def autoname(doc, method=None):
	if doc.get("__newname"):
		doc.name = doc.get("__newname")
		return

	normalize_item_group_hierarchy(doc)

	# doc.name = get_next_value(doc)

	for field in reversed(ITEM_GROUP_FIELDS):
		group_name = doc.get(field)
		if group_name:
			group_number = frappe.db.get_value("Item Group", group_name, "item_group_number")
			if not group_number:
				frappe.throw(f"El grupo de artículos '{group_name}' no tiene un número de grupo de artículos asignado.")

			# Find next available NNN in ####-NNN format
			existing = frappe.db.sql_list("""
				SELECT item_code FROM `tabItem`
				WHERE item_code LIKE %s
			""", (f"{group_number}-%",))

			used = [int(code.split("-")[1]) for code in existing if "-" in code and code.split("-")[1].isdigit()]
			next_number = max(used or [0]) + 1

			doc.name = f"{group_number}-{str(next_number).zfill(3)}"

			doc.item_code = doc.name
			return
	frappe.throw("No se ha definido ningún grupo de artículos (1 a 5) para este artículo.")


def before_save(doc, method=None):
	normalize_item_group_hierarchy(doc)
	autoset_item_group(doc)
	update_item_tax(doc)


def validate_unique_product_hash(doc, method=None):
	product_hash = (doc.get("product_hash") or "").strip()

	# Only enforce when hash is present.
	if not product_hash:
		return

	duplicate_name = frappe.db.exists("Item", {
		"product_hash": product_hash,
		"name": ["!=", doc.name],
	})

	if not duplicate_name:
		return

	duplicate = frappe.db.get_value(
		"Item",
		duplicate_name,
		["name", "product_generator", "reference_type", "reference_name"],
		as_dict=True,
	)

	link = frappe.utils.get_link_to_form("Item", duplicate_name, duplicate_name)
	ref = ""
	if duplicate and duplicate.get("reference_type") and duplicate.get("reference_name"):
		ref = f" ({duplicate.reference_type}: {duplicate.reference_name})"
	elif duplicate and duplicate.get("product_generator"):
		ref = f" (Product Generator: {duplicate.product_generator})"

	frappe.throw(
		f"Ya existe un Item con este product_hash: {link}{ref}. "
		f"No se permite duplicar especificaciones."
	)


def autoset_item_group(doc):
	"""Will set the item_group value (the one that ERPNext knows about) based 
	on the lowest level of the custom item group fields"""
	doc.item_group = doc.custom_item_group_5 \
		or doc.custom_item_group_4 \
		or doc.custom_item_group_3 \
		or doc.custom_item_group_2 \
		or doc.custom_item_group_1


def normalize_item_group_hierarchy(doc):
	"""Populate custom Item Group levels from the selected leaf Item Group."""
	leaf_item_group = get_leaf_item_group(doc)

	if not leaf_item_group:
		return

	hierarchy = get_item_group_hierarchy(leaf_item_group)

	for idx, fieldname in enumerate(ITEM_GROUP_FIELDS):
		doc.set(fieldname, hierarchy[idx] if idx < len(hierarchy) else None)

	if hierarchy:
		doc.item_group = hierarchy[-1]


def get_leaf_item_group(doc):
	"""Return the deepest selected Item Group from item_group and custom fields."""
	candidates = [
		doc.get("item_group"),
		*(doc.get(fieldname) for fieldname in reversed(ITEM_GROUP_FIELDS)),
	]

	deepest = None
	deepest_level = -1

	for item_group in candidates:
		if not item_group:
			continue

		level = len(get_item_group_hierarchy(item_group))
		if level > deepest_level:
			deepest = item_group
			deepest_level = level

	return deepest


def get_item_group_hierarchy(leaf_item_group):
	"""Return the parent chain from business root to leaf, excluding ERPNext's tree root."""
	hierarchy = []
	current = leaf_item_group

	while current:
		row = frappe.db.get_value(
			"Item Group",
			current,
			["name", "parent_item_group"],
			as_dict=True,
		)

		if not row:
			frappe.throw(f"El grupo de artículos '{current}' no existe.")

		if row.parent_item_group:
			hierarchy.append(row.name)

		current = row.parent_item_group

	hierarchy.reverse()

	if len(hierarchy) > len(ITEM_GROUP_FIELDS):
		hierarchy = hierarchy[-len(ITEM_GROUP_FIELDS):]

	return hierarchy


def update_item_tax(doc):
	# allow the developer to prevent the taxes from being overriden at
	# the item level (they just need to add a dont_override_taxes field to the doc)
	# and set it to True (or 1) to prevent the taxes from being overriden at the item level
	dont_override_taxes = getattr(doc, "dont_override_taxes", False)

	if dont_override_taxes:
		return
	
	# we will use the item_group value to update the taxes.
	# we basically use the closest parent that has taxes defined
	# and we will copy those taxes to the item
	item_group = frappe.get_doc("Item Group", doc.item_group)


	if item_group.taxes:
		doc.taxes = [] # empty only if the item_group has taxes defined

		for tax in item_group.taxes:
			doc.append("taxes", frappe.copy_doc(tax))
	else:
		# if the item_group doesn't have taxes defined
		# we will check the parent item groups until we find
		# one that has taxes defined
		parent_item_group = get_parent_item_group(item_group.name)

		while parent_item_group:
			if parent_item_group.taxes:
				doc.taxes = [] # clear the taxes only if we found a parent with taxes

				for tax in parent_item_group.taxes:
					doc.append("taxes", frappe.copy_doc(tax))

				break

			parent_item_group = get_parent_item_group(parent_item_group.name)


def get_parent_item_group(name):
	doctype = "Item Group"

	parent = frappe.get_value(doctype, name, "parent_item_group")

	if parent:
		return frappe.get_doc(doctype, parent)
	
	return None


def get_next_value(doc):
	serie = get_serie(doc)

	last_value = get_last_value(serie)

	next_value = last_value + 1

	return f"{serie}-{next_value:04d}".upper()


def get_serie(doc):
	# based on the first two characters of each item_group level
	# we will determine the serie of the item

	out = []

	for item_group in [
		doc.custom_item_group_1,
		doc.custom_item_group_2,
		doc.custom_item_group_3,
		doc.custom_item_group_4,
		doc.custom_item_group_5,
	]:
		if item_group:
			_item_group = re.sub(r"[^a-zA-Z0-9 ]", "", item_group)
			parts = _item_group.split(" ")

			if len(parts) > 1: # take the first two chars of each word
				out.append("".join([
					part[:2] for part in parts
				]))
			else:
				out.append(_item_group[:3])

	return "".join(out)


def get_last_value(serie):
	# from a list of values like:
	# ['PrCaPl-0001', 'PrCaPl-0002', 'PrCaPl-0003']
	# we will return the max value
	
	serie = serie.replace("(", "") \
		.replace(")", "") \
		.replace("[", "") \
		.replace("]", "") \
		.replace("{", "") \
		.replace("}", "") \
		.replace(" ", "")

	query = f"""
		Select
			Max(name)
		From
			`tabItem`
		Where
			name Rlike "{serie}-[0-9]+"
	"""

	result = frappe.db.sql_list(query, debug=False)

	if result:
		[lastval] = result

		if not lastval:
			return 0

		# ABCEDE-0001 => [ABCEDE, 0001]
		# we care about the second part only
		naming_parts = lastval.split("-")

		return cint(
			naming_parts[1]
		)

	# if not result it means this is the first item
	# in the serie
	return 0
