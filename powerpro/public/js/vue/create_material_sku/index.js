// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.provide("power.ui");
frappe.provide("power.utils");

const { round_to_nearest_eighth } = power.utils;

power.ui.CreateMaterialSKU = function(docname) {
	let dialog;
	let item_group_details;
	let doc;

	const url = "/api/method/powerpro.controllers.assets.item_group.get_all_item_groups";
	fetch(url)
		.then(response => response.json())
		.then(({ message }) => {
			item_group_details = message;
		});
	
	fetch(`/api/resource/Raw Material/${docname}`)
		.then(response => response.json())
		.then(({ message }) => {
			doc = message;

			if (doc.base_material === "Paper") {
				
			}
		});

	
	dialog = frappe.prompt([
		{
			fieldtype: "Section Break",
			label: __("Material Specification"),
		},
		{
			fieldname: "material_format",
			fieldtype: "Select",
			label: __("Material Format"),
			reqd: 1,
			default: "Roll",
			options: [
				"Roll",
				"Sheet",
			],
			change(event) {
				dialog.set_df_property("roll_width", "reqd", event.target.value === "Roll");
				dialog.set_df_property("roll_width", "hidden", event.target.value === "Sheet");
				dialog.set_df_property("sheet_width", "reqd", event.target.value === "Sheet");
				dialog.set_df_property("sheet_width", "hidden", event.target.value === "Roll");
				dialog.set_df_property("sheet_height", "reqd", event.target.value === "Sheet");
				dialog.set_df_property("sheet_height", "hidden", event.target.value === "Roll");
			}
		},
		{ fieldtype: "Column Break" },
		{
			fieldname: "roll_width",
			fieldtype: "Float",
			label: `${__("Roll Width")} (in)`,
			reqd: 1,
			precision: 3,
			async change(event) {
				const { target } = event;
				await frappe.timeout(.1);

				const value = round_to_nearest_eighth(target.value);
				if (target.value !== value) {
					target.value = value;
				}
			},
		},
		{
			fieldname: "sheet_width",
			fieldtype: "Float",
			label: `${__("Sheet Width")} (in)`,
			hidden: 1,
			precision: 3,
			async change(event) {
				const { target } = event;
				await frappe.timeout(.1);

				const value = round_to_nearest_eighth(target.value);
				if (target.value !== value) {
					target.value = value;
				}
			},
		},
		{
			fieldname: "sheet_height",
			fieldtype: "Float",
			label: `${__("Sheet Height")} (in)`,
			hidden: 1,
			precision: 3,
			async change(event) {
				const { target } = event;
				await frappe.timeout(.1);

				const value = round_to_nearest_eighth(target.value);
				if (target.value !== value) {
					target.value = value;
				}
			},
		},
		{
			fieldtype: "Section Break",
			label: __("Weight"),
		},
		{
			fieldname: "gsm",
			fieldtype: "Int",
			non_negative: 1,
			reqd: 1,
			label: __("GSM"),
			async change(event) {
				const { target } = event;
				await frappe.timeout(.1);

				if (!target.value) {
					target.value = 0;
				}

				if (
					target.value < 0
				) {
					target.value = 0;

					frappe.show_alert({
						message: __("GSM cannot be negative!"),
						indicator: "red",
					});
				}
			},
		},
		{
			fieldtype: "Section Break",
			label: __("Item Group"),
		},
		{
			fieldname: "item_group_1",
			fieldtype: "Link",
			label: __("Item Group 1"),
			options: "Item Group",
			default: frappe.boot?.powerpro_settings?.root_item_group_for_raw_materials,
			read_only: Boolean(frappe.boot?.powerpro_settings?.root_item_group_for_raw_materials),
			reqd: 1,
			change(event) {},
		},
		{
			fieldname: "item_group_2",
			fieldtype: "Link",
			label: __("Item Group 2"),
			options: "Item Group",
			reqd: 1,
			get_query() {
				return {
					filters: {
						parent_item_group: dialog.get_value("item_group_1"),
					},
				};
			},
			change(event) {
				// toggle visibility of the next field based on the value of this field
				// and if it's a group or not
				const { value } = this;

				if (value) {
					// const item_group = item_group_details.find(item_group => item_group.name === value);
					// const is_group = item_group?.is_group;
					const has_children = item_group_details.find(item_group => item_group.parent_item_group === value);

					dialog.set_df_property("item_group_3", "hidden", !has_children);
					dialog.set_df_property("item_group_3", "reqd", has_children);
				} else {
					dialog.set_df_property("item_group_5", "hidden", 1);
					dialog.set_df_property("item_group_3", "reqd", 0);
				}

				dialog.set_value("item_group_3", null);
			},
		},
		{
			fieldname: "item_group_3",
			fieldtype: "Link",
			label: __("Item Group 3"),
			options: "Item Group",
			hidden: 1,
			get_query() {
				return {
					filters: {
						parent_item_group: dialog.get_value("item_group_2"),
					},
				};
			},
			change(event) {
				// toggle visibility of the next field based on the value of this field
				// and if it's a group or not
				const { value } = this;

				if (value) {
					// const item_group = item_group_details.find(item_group => item_group.name === value);
					// const is_group = item_group?.is_group;
					const has_children = item_group_details.find(item_group => item_group.parent_item_group === value);

					dialog.set_df_property("item_group_4", "hidden", !has_children);
					dialog.set_df_property("item_group_4", "reqd", has_children);
				} else {
					dialog.set_df_property("item_group_4", "hidden", 1);
					dialog.set_df_property("item_group_4", "reqd", 0);
				}
								
				dialog.set_value("item_group_4", null);
			},
		},
		{
			fieldname: "item_group_4",
			fieldtype: "Link",
			label: __("Item Group 4"),
			options: "Item Group",
			hidden: 1,
			get_query() {
				return {
					filters: {
						parent_item_group: dialog.get_value("item_group_3"),
					},
				};
			},
			change(event) {
				// toggle visibility of the next field based on the value of this field
				// and if it's a group or not
				const { value } = this;

				if (value) {
					// const item_group = item_group_details.find(item_group => item_group.name === value);
					// const is_group = item_group?.is_group;
					const has_children = item_group_details.find(item_group => item_group.parent_item_group === value);

					dialog.set_df_property("item_group_5", "hidden", !has_children);
					dialog.set_df_property("item_group_5", "reqd", has_children);
				} else {
					dialog.set_df_property("item_group_5", "hidden", 1);
					dialog.set_df_property("item_group_5", "reqd", 0);
				}
								
				dialog.set_value("item_group_5", null);
			},
		},
		{
			fieldname: "item_group_5",
			fieldtype: "Link",
			label: __("Item Group 5"),
			options: "Item Group",
			hidden: 1,
			get_query() {
				return {
					filters: {
						parent_item_group: dialog.get_value("item_group_4"),
					},
				};
			},
			change(event) {},
		},
	], function(values) {
		frappe.call("powerpro.manufacturing_pro.doctype.raw_material.client.create_material_sku", {
			material_id: docname,
			...values,
		}).then(function(response) {
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
	}, __("Create a new SKU"), __("Please, do!"));
}