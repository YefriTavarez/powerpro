# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


def boot_session(bootinfo):
	bootinfo.powerpro_settings = get_powerpro_settings()
	bootinfo.roll_conversion_order_settings = get_roll_conversion_order_settings()


def get_powerpro_settings():
	settings = frappe.get_single("Power-Pro Settings")

	return {
		"root_item_group_for_raw_materials": settings.root_item_group_for_raw_materials,
		"project_manager": get_project_manager(),
	}


def get_project_manager():
	"""Get the project manager from the settings"""
	settings = frappe.get_single("Projects Settings")

	return settings.project_manager or "System Manager"


def get_roll_conversion_order_settings():
	"""Get the roll conversion order settings from the settings"""
	if frappe.db.exists("DocType", "Roll Conversion Order Settings"):
		settings = frappe.get_single("Roll Conversion Order Settings")

		return {
			"default_conversion_source_warehouse": settings.default_conversion_source_warehouse,
			"default_conversion_target_warehouse": settings.default_conversion_target_warehouse,
			"scrap_percentage": settings.scrap_percentage,
		}

	return None
