// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.provide("power.ui");
frappe.provide("power.utils");

const { round_to_nearest_eighth } = power.utils;

power.ui.CreateMaterialSKU = function(docname) {
	let theprompt;
	theprompt = frappe.prompt([
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
				theprompt.set_df_property("roll_width", "reqd", event.target.value === "Roll");
				theprompt.set_df_property("roll_width", "hidden", event.target.value === "Sheet");
				theprompt.set_df_property("sheet_width", "reqd", event.target.value === "Sheet");
				theprompt.set_df_property("sheet_width", "hidden", event.target.value === "Roll");
				theprompt.set_df_property("sheet_height", "reqd", event.target.value === "Sheet");
				theprompt.set_df_property("sheet_height", "hidden", event.target.value === "Roll");
			}
		},
		{ fieldtype: "Column Break" },
		{
			fieldname: "roll_width",
			fieldtype: "Float",
			label: __("Roll Width"),
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
			label: __("Sheet Width"),
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
			label: __("Sheet Height"),
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
		}
	], function(values) {
		frappe.call("powerpro.manufacturing_pro.doctype.raw_material.client.create_material_sku", {
			material_id: docname,
			...values,
		}).then(function(response) {
			const { message } = response;

			if (message) {
				frappe.confirm(`
					Here is the SKU <strong>${message}</strong>
					<button class="btn btn-info" onclick="frappe.utils.copy_to_clipboard('${message}')">Copy to Clipboard</button>
					<br>Do you want me to take you there?
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
					() => theprompt.show(),
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
				() => theprompt.show(),
				() => frappe.show_alert(__("Okay!")),
			);
		});
	}, "Create a new SKU", "Please, do!");
}