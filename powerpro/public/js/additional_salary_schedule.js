/* Server-side calculation and validation remain authoritative. */
frappe.ui.form.on("Additional Salary", {
    refresh(frm) { show_recurring_application(frm); },
    is_recurring(frm) { show_recurring_application(frm); },
    pp_recurring_distribution(frm) { show_recurring_application(frm); },
});

function show_recurring_application(frm) {
    const active = !!frm.doc.is_recurring;
    const configured = !!frm.doc.pp_recurring_distribution;
    frm.toggle_display("pp_recurring_distribution", active);
    frm.toggle_display("pp_recurring_distribution_from", active && configured);
    frm.toggle_reqd("pp_recurring_distribution_from", active && configured);
    frm.set_df_property("amount", "description", active && configured
        ? __("Importe mensual base. Se aplica según la quincena seleccionada; se conservan las reglas del componente salarial.")
        : "");
    // Do not clear or replace dashboard messages owned by other customizations.
}
