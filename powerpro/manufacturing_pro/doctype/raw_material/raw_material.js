// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt

{
	function refresh(frm) {
		add_custom_buttons(frm);
	}

	function add_custom_buttons(frm) {
		if (frm.doc.__islocal) {
			// buttons for new documents go here
		} else {
			// buttons for saved documents go here
			add_create_SKU_button(frm);
		}

		// always visible buttons go here
	}

	function add_create_SKU_button(frm) {
		const { doc } = frm;
		// const { round_to_nearest_eighth } = power.utils;
		frm.add_custom_button(
			__("SKU"), function() {
				return new power.ui.CreateMaterialSKU(doc.name);
			}, __("Create"));
	}

	frappe.ui.form.on("Raw Material", {
		refresh,
	});
}
