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
            frm.add_custom_button(__("Previsualizar cálculos de nómina"), () => {
                frm.trigger("show_payroll_preview");
            }, __("Acciones"));

            if (frm.doc.docstatus === 1) {
                frm.add_custom_button(__("Crear lote Banco Popular"), () => {
                    frappe.new_doc("Payroll Bank Batch", {
                        payroll_entry: frm.doc.name,
                        company: frm.doc.company,
                        currency: frm.doc.currency,
                        payment_date: frm.doc.posting_date,
                    });
                }, __("Acciones"));
            }
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

    show_payroll_preview: function (frm) {
        frappe.call({
            method: "powerpro.controllers.payroll_preflight.get_payroll_preview",
            args: { payroll_entry: frm.doc.name },
            freeze: true,
            freeze_message: __("Calculando previsualización sin guardar documentos..."),
            callback: function (r) {
                if (r.message) {
                    show_payroll_preview_dialog(r.message);
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


function show_payroll_preview_dialog(report) {
    if (report.status === "blocked") {
        show_payroll_preflight_dialog(report.preflight);
        return;
    }

    const money = (value) => format_currency(value || 0, report.currency);
    const totals = report.totals;
    const summary = `<p><strong>${__("Previsualización sin guardar")}</strong> · `
        + `${totals.employees} ${__("empleados")}</p>
        <div class="row mb-3">
            <div class="col-sm-3"><strong>${__("Bruto")}</strong><br>${money(totals.gross_pay)}</div>
            <div class="col-sm-3"><strong>${__("Deducciones")}</strong><br>${money(totals.total_deduction)}</div>
            <div class="col-sm-3"><strong>${__("Neto")}</strong><br>${money(totals.net_pay)}</div>
            <div class="col-sm-3"><strong>${__("AFP/ARS empleador")}</strong><br>${money(totals.employer_afp_ars)}</div>
        </div>`;
    const reconciliation = totals.changed_existing_slips
        ? `<p class="text-warning"><strong>${__("Reconciliación pendiente")}:</strong> `
            + `${totals.changed_existing_slips} ${__("comprobantes existentes cambiarían al recalcularse")}; `
            + `${__("diferencia neta total")}: ${money(totals.net_pay_delta)}.</p>`
        : `<p class="text-success">${__("Los netos previsualizados coinciden con los comprobantes existentes comparables.")}</p>`;

    const rows = report.rows.map((row) => `<tr>
        <td>${frappe.utils.escape_html(row.employee_name || row.employee)}</td>
        <td class="text-right">${money(row.gross_pay)}</td>
        <td class="text-right">${money(row.total_deduction)}</td>
        <td class="text-right">${money(row.net_pay)}</td>
        <td class="text-right">${row.stored_net_pay === null ? "—" : money(row.stored_net_pay)}</td>
        <td class="text-right">${row.net_pay_delta === null ? "—" : money(row.net_pay_delta)}</td>
        <td class="text-right">${money(row.employer_afp_ars)}</td>
    </tr>`).join("");
    const table = `<div class="table-responsive"><table class="table table-bordered table-sm">
        <thead><tr><th>${__("Empleado")}</th><th>${__("Bruto")}</th><th>${__("Deducciones")}</th>
        <th>${__("Neto previsto")}</th><th>${__("Neto guardado")}</th><th>${__("Diferencia")}</th>
        <th>${__("AFP/ARS empleador")}</th></tr></thead>
        <tbody>${rows}</tbody>
    </table></div>`;

    const errors = report.errors.length
        ? `<hr><p class="text-danger"><strong>${__("Errores")}</strong></p>${report.errors.map((error) =>
            `<p>${frappe.utils.escape_html(error.employee)}: ${frappe.utils.escape_html(error.message)}</p>`
        ).join("")}`
        : "";

    frappe.msgprint({
        title: __("Previsualización de nómina"),
        indicator: report.errors.length || totals.changed_existing_slips ? "orange" : "green",
        message: summary + reconciliation + table + errors,
        wide: true,
    });
}
