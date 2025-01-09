// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Cost Component", {
	setup: function (frm) {
		frm.set_query("account", "accounts", function (doc, cdt, cdn) {
			var d = locals[cdt][cdn];
			return {
				filters: {
					is_group: 0,
					company: d.company,
				},
			};
		});


		// NOT SURE WHERE THIS FIELD IS COMING FROM
		//
		// frm.set_query("earning_component_group", function () {
		// 	return {
		// 		filters: {
		// 			is_group: 1,
		// 			is_flexible_benefit: 1,
		// 		},
		// 	};
		// });
	},

	refresh: function (frm) {
		// hrms.payroll_utils.set_autocompletions_for_condition_and_formula(frm);

		if (!frm.doc.__islocal) {
			frm.trigger("add_update_structure_button");
		// 	frm.add_custom_button(
		// 		__("Cost Structure"),
		// 		() => {
		// 			frm.trigger("create_cost_structure");
		// 		},
		// 		__("Create"),
		// 	);
		}
	},

	variable_based_on_taxable_salary: function (frm) {
		if (frm.doc.variable_based_on_taxable_salary) {
			set_value_for_condition_and_formula(frm);
		}
	},

	add_update_structure_button: function (frm) {
		for (const df of ["Condition", "Formula"]) {
			frm.add_custom_button(
				__("Sync {0}", [df]),
				function () {
					frappe
						.call({
							method: "get_structures_to_be_updated",
							doc: frm.doc,
						})
						.then((r) => {
							if (r.message.length)
								frm.events.update_cost_structures(frm, df, r.message);
							else
								frappe.msgprint({
									message: __(
										"Cost Component {0} is currently not used in any Cost Structure.",
										[frm.doc.name.bold()],
									),
									title: __("No Cost Structures"),
									indicator: "orange",
								});
						});
				},
				__("Update Cost Structures"),
			);
		}
	},

	update_cost_structures: function (frm, df, structures) {
		let msg = __("{0} will be updated for the following Cost Structures: {1}.", [
			df,
			frappe.utils.comma_and(
				structures.map((d) =>
					frappe.utils.get_form_link("Cost Structure", d, true).bold(),
				),
			),
		]);
		msg += "<br>";
		msg += __("Are you sure you want to proceed?");
		frappe.confirm(msg, () => {
			frappe
				.call({
					method: "update_cost_structures",
					doc: frm.doc,
					args: {
						structures: structures,
						field: df.toLowerCase(),
						value: frm.get_field(df.toLowerCase()).value || "",
					},
				})
				.then((r) => {
					if (!r.exc) {
						frappe.show_alert({
							message: __("Cost Structures updated successfully"),
							indicator: "green",
						});
					}
				});
		});
	},

	create_cost_structure: function (frm) {
		frappe.model.with_doctype("Cost Structure", () => {
			const cost_structure = frappe.model.get_new_doc("Cost Structure");
			// const salary_detail = frappe.model.add_child(
			// 	cost_structure,
			// 	frm.doc.type === "Earning" ? "earnings" : "deductions",
			// );
			salary_detail.cost_component = frm.doc.name;
			frappe.set_route("Form", "Cost Structure", cost_structure.name);
		});
	},
});

var set_value_for_condition_and_formula = function (frm) {
	frm.set_value("formula", null);
	frm.set_value("condition", null);
	frm.set_value("amount_based_on_formula", 0);
	frm.set_value("statistical_component", 0);
	frm.set_value("do_not_include_in_total", 0);
};
