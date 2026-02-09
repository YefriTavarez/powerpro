// Copyright (c) 2025, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.provide("powerpro.masks");

{
	let form;
	const last_value = {

	};

	function setup(frm) {
		form = frm; 
		frappe.require([
			"/assets/powerpro/css/erpnext/project.css",
		]);

		_listen_on_all_fields(frm);
	}

	function refresh(frm) {
		// _set_qty_mask(frm);
		_set_queries(frm);
		_render_docfields(frm);
		add_create_buttons(frm);
	}

	function project_template(frm) {
		_render_docfields(frm);
	}

	const listen_on_field = function(frm, fieldname) {
		frappe.ui.form.on(frm.doctype, fieldname, frappe.utils.debounce(function(frm) {
			if (last_value[fieldname] === frm.doc[fieldname]) {
				return;
			}
			last_value[fieldname] = frm.doc[fieldname];
			_update_project_name({ frm, fieldname });
		}), 1000);
	}

	function _listen_on_all_fields(frm) {
		const { fields } = frm;

		fields
			.map(({ df }) => df)
			.filter(df => !frappe.model.no_value_type.includes(df.fieldtype))
			.map(function({ fieldname }) {
				return listen_on_field(frm, fieldname);
			});
	}

	function _render_docfields(frm) {
		const { doc } = frm;

		// if (!doc.project_template) {
		// 	return ; // Do nothing
		// }

		frappe.call({
			method: "powerpro.controllers.project_template.get_project_docfields",
			args: {
				"project_template_id": frm.doc.project_template,
			},
			callback({ message: docfields }) {
				for (const docfield of docfields) {
					const { fieldname, read_only, reqd, hidden, set_only_once } = docfield;

					for (
						const { property, value } of [
							{ property: "read_only", value: read_only },
							{ property: "reqd", value: reqd },
							{ property: "hidden", value: hidden },
							{ property: "set_only_once", value: set_only_once },
						]
					) {
						frm.set_df_property(fieldname, property, value);
					}
				}
			},
		});
	}

	function _update_project_name({
		frm,
		fieldname = null,
		for_validate = false,
	} = {}) {
		const { doc }  = frm;

		if (!doc[fieldname]) {
			// ToDo: Remove this
		}

		frm.call("render_project_name", { for_validate }, function() {
			if (!for_validate) {
				frm.dirty();
			}
		});
	}

	function _set_queries(frm) {
		frappe.run_serially([
			() => {
				const fieldname = "project_template";
				const get_query = function () {
					const filters = {
						"project_type": frm.doc.project_type || "",
					};

					return { filters };
				};

				frm.set_query(fieldname, get_query);
			},
		]);
	}

	frappe.realtime.on("attachment_upload_completed", function(data) {
		// const { doc } = form;
		if (form.doc.__unsaved) {
			form.dashboard.clear_headline();
			form.dashboard.set_headline_alert(
				__("This form has been modified after you have loaded it") +
					'<button class="btn btn-xs btn-primary pull-right" onclick="cur_frm.reload_doc()">' +
					__("Refresh") +
					"</button>",
				"alert-warning"
			);
		} else {
			form.debounced_reload_doc();
		}
	});

	

	function add_create_buttons(frm) {
		const { doc } = frm;
		console.log("doc", doc);
		if (!doc) {
			console.log("doc is not found");
			return;
		}

		const has_required = !!(doc.sales_order && doc.sku_producto);
		if (!has_required) {
			console.log("has_required is false");
			return;
		}

		if (frappe.model.can_create("Delivery Note")) {
			console.log("can create delivery note");
			frm.add_custom_button(
				__("Delivery Note"),
				() => prompt_and_make(frm, "dn"),
				__("Create")
			);
		}

		if (frappe.model.can_create("Sales Invoice")) {
			console.log("can create sales invoice");
			frm.add_custom_button(
				__("Sales Invoice"),
				() => prompt_and_make(frm, "si"),
				__("Create")
			);
		}
	}

	function prompt_and_make(frm, type) {
		const title = type === "dn" ? __("Create Delivery Note") : __("Create Sales Invoice");
		const d = new frappe.ui.Dialog({
			title,
			fields: [
				{
					fieldtype: "Float",
					fieldname: "qty",
					label: __("Quantity"),
					reqd: 1,
					default: cur_frm?.doc?.cantidad_a_producir || 0,
				},
			],
			primary_action_label: __("Create"),
			primary_action(values) {
				if (!values || !values.qty || flt(values.qty) <= 0) {
					frappe.msgprint({
						message: __("Please enter a quantity greater than 0"),
						title: __("Invalid Quantity"),
						indicator: "red",
					});
					return;
				}

				const method =
					type === "dn"
						? "powerpro.controllers.project.project.make_delivery_note_from_project"
						: "powerpro.controllers.project.project.make_sales_invoice_from_project";

				frappe.model.open_mapped_doc({
					method,
					args: {
						project: frm.doc.name,
						item_code: frm.doc.sku_producto,
						qty: values.qty,
						sales_order: frm.doc.sales_order || "",
					},
					frm: frm,
					freeze: true,
					freeze_message:
						type === "dn"
							? __("Creating Delivery Note ...")
							: __("Creating Sales Invoice ..."),
				});

				d.hide();
			},
		});

		d.show();
	}
frappe.ui.form.on("Project", {
		setup,
		refresh,
		project_template,
	});
}