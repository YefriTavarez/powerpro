// Copyright (c) 2026, PowerPro contributors

frappe.ui.form.on("Payroll Bank Batch", {
    setup(frm) {
        frm.set_query("payroll_entry", () => ({
            filters: { docstatus: 1 },
        }));
        frm.set_query("profile", () => ({
            filters: {
                company: frm.doc.company,
                enabled: 1,
            },
        }));
    },

    refresh(frm) {
        if (frm.is_new() || frm.doc.docstatus === 2) return;

        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__("Cargar pagos sometidos"), () => {
                frm.call({
                    method: "load_payments",
                    freeze: true,
                    freeze_message: __("Validando y cargando comprobantes sometidos..."),
                }).then(() => frm.reload_doc());
            }, __("Acciones"));
        }

        if (frm.doc.docstatus === 1 && frm.doc.status === "Approved") {
            frm.add_custom_button(__("Generar TXT privado"), () => {
                frappe.confirm(
                    __("Se generará el TXT inmutable de este lote. Esta acción no lo sube al banco y no crea asientos contables."),
                    () => {
                        frm.call({
                            method: "generate_file",
                            freeze: true,
                            freeze_message: __("Generando y verificando el TXT..."),
                        }).then((r) => {
                            const result = r.message || {};
                            frappe.show_alert({
                                message: __("TXT generado: {0}", [result.file_name]),
                                indicator: "green",
                            });
                            frm.reload_doc();
                        });
                    }
                );
            }, __("Acciones"));
        }

        if (frm.doc.generated_file) {
            frm.add_custom_button(__("Descargar TXT"), () => {
                window.open(frm.doc.generated_file, "_blank", "noopener");
            }, __("Acciones"));
        }
    },

    payroll_entry(frm) {
        if (!frm.doc.payroll_entry) return;
        frappe.db.get_value(
            "Payroll Entry",
            frm.doc.payroll_entry,
            ["company", "currency", "posting_date"]
        ).then((r) => {
            const values = r.message || {};
            return frm.set_value({
                company: values.company,
                currency: values.currency,
                payment_date: frm.doc.payment_date || values.posting_date,
            });
        }).then(() => frm.trigger("set_default_profile"));
    },

    company(frm) {
        frm.trigger("set_default_profile");
    },

    set_default_profile(frm) {
        if (!frm.doc.company || frm.doc.profile) return;
        frappe.call({
            method: "powerpro.power_pro.doctype.payroll_bank_batch.payroll_bank_batch.get_default_profile",
            args: { company: frm.doc.company },
        }).then((r) => {
            if (r.message) frm.set_value("profile", r.message);
        });
    },
});
