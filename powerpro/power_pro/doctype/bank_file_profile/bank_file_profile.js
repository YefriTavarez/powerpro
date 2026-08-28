// Copyright (c) 2026, PowerPro contributors

frappe.ui.form.on("Bank File Profile", {
    company(frm) {
        if (!frm.doc.company) return;
        frappe.db.get_value("Company", frm.doc.company, ["tax_id", "company_name"]).then((r) => {
            const values = r.message || {};
            if (!frm.doc.company_identification && values.tax_id) {
                frm.set_value("company_identification", values.tax_id);
            }
            if (!frm.doc.registered_company_name && values.company_name) {
                frm.set_value("registered_company_name", values.company_name);
            }
        });
    },
});
