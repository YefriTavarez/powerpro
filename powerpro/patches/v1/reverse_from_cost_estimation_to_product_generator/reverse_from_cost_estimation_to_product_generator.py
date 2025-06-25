# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe

from .helper import create_product_generator_from_record

def execute():
	# get current folder path
	curpath = get_current_folder_path()
	filename = f"{curpath}/records.json"

	with open(filename, "r", encoding="utf-8") as file:
		import json
		records = json.load(file)

		print(records[0]["json"])

		for record in records:
			print(f"Creating {record['name']}...")
			doc = create_product_generator_from_record(record["json"])
			doc.item_asociado = record["name"]
			# doc.db_update()
			# frappe.db.commit()

			try:
				doc.save()
			except Exception as e:
				frappe.db.rollback()
				print(f"Error saving {record['name']}: {e}")
			else:
				item = frappe.get_doc("Item", record["name"])
				item.product_hash = doc.product_hash

				item.add_comment("Edit", f"Unlinked From '{item.reference_type} > {item.reference_name}' to 'Product Generator > {doc.name}'")
				item.reference_type = "Product Generator"
				item.reference_name = doc.name

				item.save()
				frappe.db.commit()
				print(f"{record['name']} created successfully.")


def get_current_folder_path():
	"""Get the current folder path of this script."""
	import os
	import inspect

	current_file_path = os.path.abspath(inspect.getfile(inspect.currentframe()))
	return os.path.dirname(current_file_path)