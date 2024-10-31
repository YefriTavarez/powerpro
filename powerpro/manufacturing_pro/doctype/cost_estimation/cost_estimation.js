// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt

{
	frappe.provide("power.ui");

	function _setup_vue(frm) {
		frappe.require([
			"powerpro.bundle.js",
		], function() {
			const selector = `div[data-fieldname="cost_estimation_app"]`;
			
			if (!power.ui.CostEstimation) {
				jQuery(
					selector
				).html(
					`<p class="text-muted" style="color: rgb(181, 42, 42) !important">
						${__("Error while loading Cost Estimation")}
					</p>`
				);

				frappe.show_alert({
					message: "Vue.CostEstimation is not available!",
					indicator: "red",
				});

				return ; // exit
			}

			power.ui.cost_estimation = new power.ui.CostEstimation(frm, selector);
		});
	}

	function setup(frm) {
		_setup_vue(frm);
	}

	function raw_material(frm) {
		const { cost_estimation } = power.ui;
		cost_estimation.fetch_raw_material_specs();
	}

	frappe.ui.form.on("Cost Estimation", {
		setup,
		raw_material,
	});
}