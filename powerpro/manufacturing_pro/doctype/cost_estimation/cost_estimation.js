// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt

{
	frappe.provide("power.ui");

	function _setup_vue(frm) {
		frappe.require([
			"powerpro.bundle.js",
		], function() {
			const selector = `div[data-fieldname="cost_estimation_app"]`;
			
			if (!power.ui.CostEstimationApp) {
				jQuery(
					selector
				).html(
					`<p class="text-muted" style="color: rgb(181, 42, 42) !important">
						${__("Error while loading Cost Estimation")}
					</p>`
				);

				frappe.show_alert({
					message: "Vue.CostEstimationApp is not available!",
					indicator: "red",
				});

				return ; // exit
			}

			power.ui.cost_estimation = new power.ui.CostEstimationApp(frm, selector);
		});
	}

	function _autoset_expires_on({ frm, force = false }) {
		// sets the expires on based on the created_on (if set)
		// otherwise, sets the expires on based on the current date + 30 days
		// if not created_on is set and created_on is set and force is false, then do nothing
		// if created_on is set and force is true, then set the expires_on based on the created_on

		const { doc } = frm;
		const { add_days } = frappe.datetime;

		if (!doc.created_on) {
			if (force) {
				doc.expires_on = add_days(frappe.datetime.now_date(), 30);
			}
		} else {
			doc.expires_on = add_days(doc.created_on, 30);
		}

		frm.refresh_field("expires_on");
	}

	function _validate_expires_on(frm) {
		// validate expires_on is never less than created_on (if set)
		// if created_on is not set, then let's make sure it is not less than the current date

		const { doc } = frm;

		if (!doc.created_on) {
			if (doc.expires_on < frappe.datetime.now_date()) {
				frappe.msgprint(__("Expires On cannot be less than the current date!"));
			}
		} else if (doc.expires_on < doc.created_on) {
			frappe.msgprint(__("Expires On cannot be less than Created On!"));
		}
	}

	function setup(frm) {
		_setup_vue(frm);
	}

	function refresh(frm) {
		// const { vm } = power.ui.cost_estimation;
		// vm.$refs.
	}

	function raw_material(frm) {
		const { cost_estimation } = power.ui;
		cost_estimation.fetch_raw_material_specs();
	}

	function onload_post_render(frm) {
		_autoset_expires_on({ frm });
	}

	function created_on(frm) {
		// update expires_on
		_autoset_expires_on({ frm, force: true });
	}

	function expires_on(frm) {
		_validate_expires_on(frm);
	}

	function data(frm) {
		
	}

	frappe.ui.form.on("Cost Estimation", {
		setup,
		refresh,
		onload_post_render,
		raw_material,
		created_on,
		expires_on,
		data,
	});
}