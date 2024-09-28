// Copyright (c) 2024, Miguel Higuera and Contributors
// For license information, please see license.txt

frappe.ui.form.off("Salary Structure", "refresh", "toggle_fields");
frappe.ui.form.off("Salary Structure", "toggle_fields");

frappe.ui.form.on("Salary Structure", {
    refresh(frm) {
        frm.trigger("toggle_reqd_fields");
    },

	toggle_reqd_fields: function (frm) {
		frm.toggle_display(
			["salary_component", "hour_rate"],
			frm.doc.salary_slip_based_on_timesheet,
		);
		frm.toggle_reqd(["salary_component", "hour_rate"], 0);
		frm.toggle_reqd(["payroll_frequency"], 1);
	},
});