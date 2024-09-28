// Copyright (c) 2024, Miguel Higuera and Contributors
// For license information, please see license.txt


// frappe.ui.form.off("Payroll Entry", "salary_slip_based_on_timesheet");

frappe.ui.form.on("Payroll Entry", {
    refresh(frm) {
        frm.trigger("toggle_reqd_fields");
    },

    salary_slip_based_on_timesheet: function (frm) {
        frm.trigger("toggle_reqd_fields");
    },

    payroll_frequency: function (frm) {
        frm.trigger("set_start_end_dates").then(() => {
			frm.events.clear_employee_table(frm);
		});
    },

    toggle_reqd_fields: function (frm) {
        frm.toggle_reqd(["payroll_frequency"], 1);
    },

    set_start_end_dates: function (frm) {
        frappe.call({
            method: "hrms.payroll.doctype.payroll_entry.payroll_entry.get_start_end_dates",
            args: {
                payroll_frequency: frm.doc.payroll_frequency,
                start_date: frm.doc.posting_date,
            },
            callback: function (r) {
                if (r.message) {
                    in_progress = true;
                    frm.set_value("start_date", r.message.start_date);
                    frm.set_value("end_date", r.message.end_date);
                }
            },
        });
    },

});