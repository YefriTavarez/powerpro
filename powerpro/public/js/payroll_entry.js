// Copyright (c) 2024, Miguel Higuera and Contributors
// For license information, please see license.txt


// frappe.ui.form.off("Payroll Entry", "salary_slip_based_on_timesheet");

frappe.ui.form.on("Payroll Entry", {
    refresh(frm) {
        frm.trigger("toggle_reqd_fields");

        if (!frm.is_new()) {
            frm.add_custom_button(__("Validar preparación de nómina"), () => {
                frm.trigger("show_payroll_preflight");
            }, __("Acciones"));
        }
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
        return frappe.call({
            method: "hrms.payroll.doctype.payroll_entry.payroll_entry.get_start_end_dates",
            args: {
                payroll_frequency: frm.doc.payroll_frequency,
                start_date: frm.doc.posting_date,
            },
            callback: function (r) {
                if (r.message) {
                    frm.set_value("start_date", r.message.start_date);
                    frm.set_value("end_date", r.message.end_date);
                }
            },
        });
    },

    show_payroll_preflight: function (frm) {
        frappe.call({
            method: "powerpro.controllers.payroll_preflight.get_payroll_preflight",
            args: { payroll_entry: frm.doc.name },
            freeze: true,
            freeze_message: __("Validando preparación de nómina..."),
            callback: function (r) {
                if (r.message) {
                    show_payroll_preflight_dialog(r.message);
                }
            },
        });
    },
});


function show_payroll_preflight_dialog(report) {
    const severity = {
        blocker: { label: __("Bloqueo"), color: "red" },
        warning: { label: __("Advertencia"), color: "orange" },
        info: { label: __("Información"), color: "blue" },
    };
    const status = {
        blocked: { label: __("No está listo"), indicator: "red" },
        ready_with_warnings: { label: __("Listo con advertencias"), indicator: "orange" },
        ready: { label: __("Listo"), indicator: "green" },
    }[report.status];

    const summary = `<p><strong>${frappe.utils.escape_html(status.label)}</strong> · `
        + `${report.summary.employees} ${__("empleados")} · `
        + `${report.summary.blockers} ${__("bloqueos")} · `
        + `${report.summary.warnings} ${__("advertencias")}</p>`;

    const issues = report.issues.map((issue) => {
        const style = severity[issue.severity];
        const records = issue.records.length
            ? `<div class="text-muted small">${issue.records.map((record) => frappe.utils.escape_html(record)).join("<br>")}</div>`
            : "";
        return `<div class="mb-3">
            <span class="indicator-pill ${style.color}">${frappe.utils.escape_html(style.label)}</span>
            <strong>${frappe.utils.escape_html(issue.title)}</strong>
            <div>${frappe.utils.escape_html(issue.message)}</div>
            ${records}
        </div>`;
    }).join("");

    frappe.msgprint({
        title: __("Validación de nómina"),
        indicator: status.indicator,
        message: summary + (issues || `<p>${__("No se encontraron observaciones.")}</p>`),
        wide: true,
    });
}
