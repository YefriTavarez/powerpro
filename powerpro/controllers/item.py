# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe
from frappe.utils import cint


def autoname(doc, method=None):
	doc.name = get_next_value(doc)


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
	# we will determine the serie

	return "".join([
		item_group[:2] for item_group in [
			doc.custom_item_group_1,
			doc.custom_item_group_2,
			doc.custom_item_group_3,
			doc.custom_item_group_4,
			doc.custom_item_group_5
		] if item_group
	])

	
def get_last_value(serie):
	# from a list of values like:
	# ['PrCaPl-0001', 'PrCaPl-0002', 'PrCaPl-0003']
	# we will return the max value
	result = frappe.db.sql_list(f"""
		Select
			Max(name)
		From
			`tabItem`
		Where
			name Rlike "{serie}-[0-9]+"
	""")

	if result:
		rezult = result[0]

		if not rezult:
			return 0

		return cint(rezult.split("-")[1])

	return 0
