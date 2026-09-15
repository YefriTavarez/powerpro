// Copyright (c) 2026, PowerPro contributors

frappe.ui.form.on("Supplier Retainer Agreement", {
    setup(frm) {
        frm.set_query("supplier", () => ({ filters: { disabled: 0 } }));
        frm.set_query("item", () => ({
            filters: { disabled: 0, is_stock_item: 0, is_purchase_item: 1 },
        }));
        frm.set_query("expense_account", () => ({
            filters: { company: frm.doc.company, is_group: 0, root_type: "Expense", disabled: 0 },
        }));
        frm.set_query("cost_center", () => ({
            filters: { company: frm.doc.company, is_group: 0, disabled: 0 },
        }));
        frm.set_query("taxes_and_charges", () => ({
            filters: { company: frm.doc.company, disabled: 0 },
        }));
    },

    refresh(frm) {
        const can_change_submitted_template = ["Accounts Manager", "System Manager"]
            .some((role) => frappe.user_roles.includes(role));
        frm.set_df_property("taxes_and_charges", "read_only",
            frm.doc.docstatus === 1 && !can_change_submitted_template);
        frm.add_custom_button(__("Ver liquidaciones"), () => {
            frappe.set_route("List", "Supplier Retainer Batch");
        }, __("Ir a"));

        if (frm.doc.docstatus === 1) {
            frm.set_intro(__("Acuerdo validado. Los cambios autorizados de plantilla se aplican a nuevas facturas; las ya creadas conservan sus impuestos."), "blue");
            frm.add_custom_button(__("Preparar liquidación"), () => {
                frappe.new_doc("Supplier Retainer Batch", {
                    company: frm.doc.company,
                    currency: frm.doc.currency,
                    supplier: frm.doc.supplier,
                    frequency: frm.doc.frequency,
                });
            }, __("Crear"));
        } else {
            frm.set_intro("");
        }
    },
});
