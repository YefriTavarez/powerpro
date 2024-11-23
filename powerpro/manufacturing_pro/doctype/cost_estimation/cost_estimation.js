// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt

{
	frappe.provide("power.ui.cost_estimation");

	function _setup_vue(frm) {
		frappe.require([
			"powerpro.bundle.js",
		], function() {
			_refresh_vue(frm);
		});
	}

	async function _refresh_vue(frm) {
		await frappe.timeout(0.5);
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
				message: __("Vue.CostEstimationApp is not available!"),
				indicator: "red",
			});

			return ; // exit
		}

		power.ui.cost_estimation = new power.ui.CostEstimationApp(frm, selector);
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
		_refresh_vue(frm);
		_add_custom_buttons(frm);
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
		// ToDo: validate data
	}

	function _add_custom_buttons(frm) {
		if (frm.is_new()) {
			// buttons for new documents
			_add_load_from_sku_button(frm);
		} else {
			if (frm.doc.docstatus === 0) {
				// buttons for draft documents
			} else if (frm.doc.docstatus === 1) {
				// buttons for submitted documents
				_add_create_sku_button(frm);
			} else {
				// buttons for cancelled documents
			}
		}

		// always on buttons
	}

	function _add_load_from_sku_button(frm) {
		const label = __("SKU");
		function action(event) {
			_show_load_from_sku_popup(frm);
		}
		const parent = __("Fetch From");
		frm.add_custom_button(label, action, parent);
	}

	function _show_load_from_sku_popup(frm) {
		const fields = [
			{
				fieldtype: "Link",
				fieldname: "item",
				label: __("Item"),
				options: "Item",
				description: __("Please select an Item to load from"),
				reqd: 1,
				get_query: {
					reference_type: frm.doctype,
				}
			},
		];

		function callback({ item }) {
			_load_estimation_from_sku(frm, item);
		}

		const title = __("Load from Item");
		const primary_label = __("Load");
		
		frappe.prompt(fields, callback, title, primary_label);
	}

	function _add_create_sku_button(frm) {
		const { doc } = frm;

		if (!frm.is_dirty() && !doc.__onload.smart_hash_exist) {
			frm.add_custom_button(
				__("SKU"),
				() => {
					const method = "create_sku";
					const args = {
						// no-args
					};
					
					frm.call(method, args)
						.then(function(response) {
							const { message } = response;
				
							if (message) {
								frappe.confirm(`
									${__("Here is the SKU")} <strong>${message}</strong>
									<button class="btn btn-info" onclick="frappe.utils.copy_to_clipboard('${message}')">
										${__("Copy to Clipboard")}
									</button>
									<br>${__("Do you want me to take you there?")}
								`, () => {
									frappe.set_route("Form", "Item", message);
								}, () => {
									frappe.show_alert({
										message: __("Alright... let's be productive, then!"),
										indicator: "green",
									});
								});
				
								frappe.show_alert({
									message,
									indicator: "green",
								});

								frm.reload_doc();
							} else {
								frappe.show_alert({
									message: __("SKU not created!"),
									indicator: "red",
								});
				
								frappe.confirm(
									__("Would you like to try again?"),
									() => dialog.show(),
									() => frappe.show_alert(__("Okay!")),
								);
							}
						}, function(exec) {
							frappe.show_alert({
								message: __("SKU not created!"),
								indicator: "red",
							});
				
							frappe.confirm(
								__("Would you like to try again?"),
								() => dialog.show(),
								() => frappe.show_alert(__("Okay!")),
							);
						});
				},
				__("Create")
			);
		}
	}

	function _load_estimation_from_sku(frm, sku) {
		const doctype = "Item";
		const name = sku;
		const fieldname = "product_details";
		function callback({ product_details: value }) {
			function __onerror() {
				frappe.msgprint(
					__("Woops! It looks like this SKU was created using an older version of the Cost Estimation.")
				);
			}

			let object = null;

			if (!value) {
				__onerror();
				return ; // exit
			} else {

				try {
					object = JSON.parse(value);
				} catch (error) {
					__onerror();
					return ; // exit
				}

				if (Object.keys(value).length === 0) {
					__onerror();
					return ; // exit
				}
			}
			
			frm.set_value("product_type", object.tipo_de_producto);
			frm.set_value("raw_material", object.material);
			
			frm.set_value("data", value);
			_refresh_vue(frm);

			frappe.show_alert({
				message: __("Estimation loaded!"),
				indicator: "green",
			});
		}
		frappe.db.get_value(doctype, name, fieldname, callback);
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