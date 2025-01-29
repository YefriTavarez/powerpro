// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.listview_settings["Raw Material"] = {
	hide_name_column: false,
	disable_comment_count: true,
	disable_auto_refresh: true,
	ignore_fields_in_listview: [
		"base_material",
	],
	button: {
		show(doc) {
			return doc.enabled;
		},
		get_label() {
			return __("Create SKU");
		},
		get_description(doc) {
			return __("Create SKU");
		},
		action(doc) {
			return new power.ui.CreateMaterialSKU(doc.name);
		},
	},
	fields: JSON.stringify([
		{fieldname: "description"},
		{fieldname: "gsm"},
		{fieldname: "base_material"},
	]),
};
