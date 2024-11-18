// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.provide("power.ui.base_material_opts");

{

	function refresh_handler(frm) {
		_add_custom_buttons(frm);
		_resfresh_base_material_options(frm);
	}
	
	function base_material_handler(frm) {
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

	async function _resfresh_base_material_options(frm) {
		const { doc } = frm;
		const { base_material: name } = doc;

		if (!name) {
			return ; // do nothing
		}

		if (
			!(name in power.ui.base_material_opts &&
			!power.ui.base_material_opts[name].length)
		) {
			// frappe.call({
			// 	method: "powerpro.controllers.assets.base_material.get_base_material_details",
			// 	args: { name },
			// 	callback({ message }) {
			// 		// apply options to this doctype from Base Material
			// 		power.ui.base_material_opts[name] = message;
			// 	}
			// });
			const url = `/api/method/powerpro.controllers.assets.base_material.get_base_material_details?name=${name}`;
			await fetch(url)
				.then(response => response.json())
				.then(({ message }) => {
					power.ui.base_material_opts[name] = message;
				});
		}

		// refresh the options
		const base_material = power.ui.base_material_opts[name];
		if (!base_material) {
			frappe.throw(
				__("Base Material {0} not found", [name])
			)
		}

		_render_option(
			frm,
			"option_1",
			base_material.option_name_1,
			base_material.options_1,
			base_material.option_name_1 && base_material.options_1
		);

		_render_option(
			frm,
			"option_2",
			base_material.option_name_2,
			base_material.options_2,
			base_material.option_name_2 && base_material.options_2
		);

		_render_option(
			frm,
			"option_3",
			base_material.option_name_3,
			base_material.options_3,
			base_material.option_name_3 && base_material.options_3
		);
	}
	

	function _add_create_SKU_button(frm) {
		const { doc } = frm;
		// const { round_to_nearest_eighth } = power.utils;
		frm.add_custom_button(
			__("SKU"), function() {
				return new power.ui.CreateMaterialSKU(doc.name);
			}, __("Create"));
	}

	function _render_option(
		frm, option_name, option_label, option_list, set
	) {
		if (set) {
			// set options to the field
			frm.set_df_property(
				option_name,
				"options",
				option_list
			);

			// update the label
			frm.set_df_property(
				option_name,
				"label",
				option_label
			);

			// show the field
			frm.toggle_display(option_name, true);
		} else {
			frm.set_df_property(
				option_name,
				"options",
				"[Select]"
			);

			// update the label
			frm.set_df_property(
				option_name,
				"label",
				frappe.unscrub(option_name)
			);

			// hide the field
			frm.toggle_display(option_name, false);
		}
	}

	frappe.ui.form.on("Raw Material", {
		refresh: refresh_handler,
		base_material: base_material_handler,
	});
}
