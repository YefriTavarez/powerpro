# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe
from frappe.utils import cint


def autoname(doc, method=None):
	if doc.get("__newname"):
		doc.name = doc.get("__newname")
		return

	doc.name = get_next_value(doc)

	if not doc.item_code:
		doc.item_code = doc.name


def before_save(doc, method=None):
	autoset_item_group(doc)
	update_item_tax(doc)


def autoset_item_group(doc):
	"""Will set the item_group value (the one that ERPNext knows about) based 
	on the lowest level of the custom item group fields"""
	doc.item_group = doc.custom_item_group_5 \
		or doc.custom_item_group_4 \
		or doc.custom_item_group_3 \
		or doc.custom_item_group_2 \
		or doc.custom_item_group_1


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
			parts = item_group.split(" ")

			if len(parts) > 1: # take the first two chars of each word
				out.append("".join([
					part[:2] for part in parts
				]))
			else:
				out.append(item_group[:3])

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
