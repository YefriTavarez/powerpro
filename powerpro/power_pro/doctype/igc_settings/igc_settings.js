// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on("IGC Settings", {
	setup(frm) {
		const company = (cdt, cdn) => locals[cdt][cdn].company || "";
		frm.set_query("expense_account", "dieta_companies", (doc, cdt, cdn) => ({
			filters: { company: company(cdt, cdn), is_group: 0, disabled: 0, root_type: "Expense" },
		}));
		frm.set_query("payment_account", "dieta_payment_methods", (doc, cdt, cdn) => ({
			filters: {
				company: company(cdt, cdn), is_group: 0, disabled: 0,
				account_type: ["in", ["Cash", "Bank"]],
			},
		}));
	},
});
