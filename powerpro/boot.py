# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


def boot_session(bootinfo):
	bootinfo.powerpro_settings = get_powerpro_settings()


def get_powerpro_settings():
	settings = frappe.get_single("Power-Pro Settings")

	return {
		"root_item_group_for_raw_materials": settings.root_item_group_for_raw_materials,
	}
