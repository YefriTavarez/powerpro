# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


# path = "powerpro.controllers.assets.cost_estimation.get_all_ink_colors"

@frappe.whitelist()
def get_all_ink_colors():
	import time
	time.sleep(2)
	return frappe.get_all("Ink Color", pluck="name")

@frappe.whitelist()
def get_all_foil_colors():
	import time
	time.sleep(1.5)
	return frappe.get_all("Foil Color", pluck="name")
