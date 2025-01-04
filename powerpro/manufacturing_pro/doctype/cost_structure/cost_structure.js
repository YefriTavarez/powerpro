// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt


frappe.ui.form.on("Cost Structure", {
	onload: function (frm) {
		frm.alerted_rows = [];
	},
	currency: function (frm) {
		calculate_totals(frm.doc);
		frm.refresh();
	},

	refresh: function (frm) {
		frm.trigger("toggle_fields");
		frm.fields_dict["components"].grid.set_column_disp("default_amount", false);
		// frm.fields_dict["deductions"].grid.set_column_disp("default_amount", false);


		// // set columns read-only
		// let fields_read_only = [
		// 	"is_tax_applicable",
		// 	"is_flexible_benefit",
		// 	"variable_based_on_taxable_salary",
		// ];
		// fields_read_only.forEach(function (field) {
		// 	frm.fields_dict.components.grid.update_docfield_property(field, "read_only", 1);
		// 	// frm.fields_dict.deductions.grid.update_docfield_property(field, "read_only", 1);
		// });
		// frm.trigger("set_earning_deduction_component");
	},

	// salary_slip_based_on_timesheet: function (frm) {
	// 	frm.trigger("toggle_fields");
	// 	hrms.set_payroll_frequency_to_null(frm);
	// },

	// preview_salary_slip: function (frm) {
	// 	frappe.call({
	// 		method: "hrms.payroll.doctype.cost_structure.cost_structure.get_employees",
	// 		args: {
	// 			cost_structure: frm.doc.name,
	// 		},
	// 		callback: function (r) {
	// 			var employees = r.message;
	// 			if (!employees) return;
	// 			if (employees.length == 1) {
	// 				frm.events.open_salary_slip(frm, employees[0]);
	// 			} else {
	// 				var d = new frappe.ui.Dialog({
	// 					title: __("Preview Salary Slip"),
	// 					fields: [
	// 						{
	// 							label: __("Employee"),
	// 							fieldname: "employee",
	// 							fieldtype: "Autocomplete",
	// 							reqd: true,
	// 							options: employees,
	// 						},
	// 						{
	// 							fieldname: "fetch",
	// 							label: __("Show Salary Slip"),
	// 							fieldtype: "Button",
	// 						},
	// 					],
	// 				});
	// 				d.get_input("fetch").on("click", function () {
	// 					var values = d.get_values();
	// 					if (!values) return;
	// 					frm.events.open_salary_slip(frm, values.employee);
	// 				});
	// 				d.show();
	// 			}
	// 		},
	// 	});
	// },

	// open_salary_slip: function (frm, employee) {
	// 	var print_format = frm.doc.salary_slip_based_on_timesheet
	// 		? "Salary Slip based on Timesheet"
	// 		: "Salary Slip Standard";
	// 	frappe.call({
	// 		method: "hrms.payroll.doctype.cost_structure.cost_structure.make_salary_slip",
	// 		args: {
	// 			source_name: frm.doc.name,
	// 			employee: employee,
	// 			as_print: 1,
	// 			print_format: print_format,
	// 			for_preview: 1,
	// 		},
	// 		callback: function (r) {
	// 			var new_window = window.open();
	// 			new_window.document.write(r.message);
	// 		},
	// 	});
	// },

	toggle_fields: function (frm) {
		frm.toggle_display(
			["cost_component", "hour_rate"],
			frm.doc.salary_slip_based_on_timesheet,
		);
		frm.toggle_reqd(["cost_component", "hour_rate"], frm.doc.salary_slip_based_on_timesheet);
		// frm.toggle_reqd(["payroll_frequency"], !frm.doc.salary_slip_based_on_timesheet);
	},
});

var validate_date = function (frm, cdt, cdn) {
	var doc = locals[cdt][cdn];
	if (doc.to_date && doc.from_date) {
		var from_date = frappe.datetime.str_to_obj(doc.from_date);
		var to_date = frappe.datetime.str_to_obj(doc.to_date);

		if (to_date < from_date) {
			frappe.model.set_value(cdt, cdn, "to_date", "");
			frappe.throw(__("From Date cannot be greater than To Date"));
		}
	}
};

// nosemgrep: frappe-semgrep-rules.rules.frappe-cur-frm-usage
cur_frm.cscript.amount = function (doc, cdt, cdn) {
	calculate_totals(doc, cdt, cdn);
};

var calculate_totals = function (doc) {
	var tbl1 = doc.components || [];
	var tbl2 = [];

	var total_earn = 0;
	var total_ded = 0;
	for (var i = 0; i < tbl1.length; i++) {
		total_earn += flt(tbl1[i].amount);
	}
	for (var j = 0; j < tbl2.length; j++) {
		total_ded += flt(tbl2[j].amount);
	}
	doc.total_earning = total_earn;
	doc.total_deduction = total_ded;
	doc.net_pay = 0.0;
	if (doc.salary_slip_based_on_timesheet == 0) {
		doc.net_pay = flt(total_earn) - flt(total_ded);
	}

	refresh_many(["total_earning", "total_deduction", "net_pay"]);
};

// nosemgrep: frappe-semgrep-rules.rules.frappe-cur-frm-usage
cur_frm.cscript.validate = function (doc, cdt, cdn) {
	calculate_totals(doc);
};

frappe.ui.form.on("Cost Detail", {
	form_render: function (frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		// ToDo: Implement this for Cost module
		// hrms.payroll_utils.set_autocompletions_for_condition_and_formula(frm, row);
	},

	amount: function (frm) {
		calculate_totals(frm.doc);
	},

	components_remove: function (frm) {
		calculate_totals(frm.doc);
	},

	// deductions_remove: function (frm) {
	// 	calculate_totals(frm.doc);
	// },

	formula: function (frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.formula && !row?.amount_based_on_formula && !frm.alerted_rows.includes(cdn)) {
			frappe.msgprint({
				message: __(
					"{0} Row #{1}: {2} needs to be enabled for the formula to be considered.",
					[toTitle(row.parentfield), row.idx, __("Amount based on formula").bold()],
				),
				title: __("Warning"),
				indicator: "orange",
			});
			frm.alerted_rows.push(cdn);
		}
	},

	cost_component: function (frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (child.cost_component) {
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "Cost Component",
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

						if (result.amount_based_on_formula == 1) {
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
						
						refresh_field("components");
					}
				},
			});
		}
	},

	amount_based_on_formula: function (frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (child.amount_based_on_formula == 1) {
			frappe.model.set_value(cdt, cdn, "amount", null);
			const index = frm.alerted_rows.indexOf(cdn);
			if (index > -1) frm.alerted_rows.splice(index, 1);
		} else {
			frappe.model.set_value(cdt, cdn, "formula", null);
		}
	},
});
