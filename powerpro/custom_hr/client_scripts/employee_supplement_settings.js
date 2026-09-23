frappe.ui.form.on("Employee Supplement Settings", {
    setup(frm) {
        frm.set_query("salary_component", "mappings", () => ({ filters: {
            type: "Earning", disabled: 0, depends_on_payment_days: 0,
            statistical_component: 0, do_not_include_in_total: 0,
        }}));
        frm.set_query("additional_salary", "existing_salaries", () => ({ filters: {
            company: frm.doc.company, currency: frm.doc.currency, docstatus: 1,
            disabled: 0, type: "Earning", overwrite_salary_structure_amount: 0,
        }}));
    },
});
