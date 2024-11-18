// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt

{
	function refresh(frm) {
		_add_custom_buttons(frm);
		_resfresh_base_material_options(frm);
	}

	function _add_custom_buttons(frm) {
		if (frm.doc.__islocal) {
			// buttons for new documents go here
		} else {
			// buttons for saved documents go here
			_add_create_SKU_button(frm);
		}

		// always visible buttons go here
	}

	function _resfresh_base_material_options(frm) {
		const { doc } = frm;
		const { base_material: name } = doc;

		if (!base_material) {
			return ; // do nothing
		}

		frappe.call({
			method: "powerpro.controllers.assets.base_material.get_base_material_details",
			args: { name },
			callback({ message }) {
				// apply options to this doctype from Base Material
			}
		});
	}
	

	function _add_create_SKU_button(frm) {
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
