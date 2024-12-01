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
	doc.item_group = doc.custom_item_group_5 \
		or doc.custom_item_group_4 \
		or doc.custom_item_group_3 \
		or doc.custom_item_group_2 \
		or doc.custom_item_group_1


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
		doc.custom_item_group_5
	]:
		if item_group:
			parts = item_group.split(" ")

			if len(parts) > 1: # take the first char of each word
				out.append("".join([
					part[0] for part in parts
				]))
			else:
				out.append(item_group[:2])

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

	frappe.errprint(query)
	result = frappe.db.sql_list(query, debug=True)

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
