// Copyright (c) 2025, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on("Cost Slip", {
	// setup: function (frm) {
	// 	$.each(["components"], function (i, table_fieldname) {
	// 		frm.get_field(table_fieldname).grid.editable_fields = [
	// 			{ fieldname: "cost_component", columns: 6 },
	// 			{ fieldname: "amount", columns: 4 },
	// 		];
	// 	});
	// },

	// refresh: function (frm) {
	// 	var salary_detail_fields = [
	// 		"formula",
	// 		"abbr",
	// 		"statistical_component",
	// 		// "amount",
	// 	];
	// 	frm.fields_dict["components"].grid.set_column_disp(salary_detail_fields, false);
	// },


	cost_structure: function (frm) {
		frm.trigger("fetch_component_details");
	},

	fetch_component_details: function (frm) {
		const { doc } = frm;

		if (doc.cost_structure) {
			frappe.call({
				method: "fetch_component_details",
				doc: doc,
				callback: function () {
					frm.refresh_fields();
				},
			});
		}
	},
});


var set_totals = function (frm) {
	if (frm.doc.docstatus === 0 && frm.doc.doctype === "Cost Slip") {
		if (frm.doc.components) {
			frappe.call({
				method: "set_totals",
				doc: frm.doc,
				callback: function () {
					frm.refresh_fields();
				},
			});
		}
	}
};

frappe.ui.form.on("Cost Detail", {
	amount: function (frm) {
		set_totals(frm);
	},

	components_remove: function (frm) {
		set_totals(frm);
	},

	cost_component: function (frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (child.cost_component) {
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "Salary Component",
					name: child.cost_component,
				},
				callback: function (data) {
					if (data.message) {
						var result = data.message;
						frappe.model.set_value(cdt, cdn, "condition", result.condition);
						frappe.model.set_value(
							cdt,
							cdn,
							"amount_based_on_formula",
							result.amount_based_on_formula,
						);
						if (result.amount_based_on_formula === 1) {
							frappe.model.set_value(cdt, cdn, "formula", result.formula);
						} else {
							frappe.model.set_value(cdt, cdn, "amount", result.amount);
						}
						frappe.model.set_value(
							cdt,
							cdn,
							"statistical_component",
							result.statistical_component,
						);
						frappe.model.set_value(
							cdt,
							cdn,
							"depends_on_payment_days",
							result.depends_on_payment_days,
						);
						frappe.model.set_value(
							cdt,
							cdn,
							"do_not_include_in_total",
							result.do_not_include_in_total,
						);
						// frappe.model.set_value(
						// 	cdt,
						// 	cdn,
						// 	"variable_based_on_taxable_salary",
						// 	result.variable_based_on_taxable_salary,
						// );
						// frappe.model.set_value(
						// 	cdt,
						// 	cdn,
						// 	"is_tax_applicable",
						// 	result.is_tax_applicable,
						// );
						// frappe.model.set_value(
						// 	cdt,
						// 	cdn,
						// 	"is_flexible_benefit",
						// 	result.is_flexible_benefit,
						// );
						refresh_field("components");
					}
				},
			});
		}
	},

	amount_based_on_formula: function (frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (child.amount_based_on_formula === 1) {
			frappe.model.set_value(cdt, cdn, "amount", null);
		} else {
			frappe.model.set_value(cdt, cdn, "formula", null);
		}
	},
});
