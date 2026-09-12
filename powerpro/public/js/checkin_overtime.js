frappe.provide("powerpro.checkin_overtime");
powerpro.checkin_overtime.add_actions = (frm) => {
    if (frm.is_new() || frm.doc.docstatus !== 1) return;
    frappe.call({method: "powerpro.controllers.checkin_overtime.get_status", args: {authorization: frm.doc.name}}).then(({message}) => {
        if (!message.enabled || !message.can_process) return;
        const enrolled = Boolean(message.evidence_enrolled);
        if (!enrolled && (frm.doc.overtime_work_call || frm.doc.reconciled_on)) return;
        frm.add_custom_button(__(enrolled ? "Procesar marcaciones" : "Inscribir conciliación por marcaciones"), () => {
            if (frm.is_dirty()) {frappe.msgprint(__("Guarde los cambios antes de procesar.")); return;}
            frappe.call({method: `powerpro.controllers.checkin_overtime.${enrolled ? "process_now" : "enroll"}`,
                type: "POST", args: {authorization: frm.doc.name}, freeze: true,
                freeze_message: __("Verificando evidencia de trabajo...")}).then(({message}) => {
                    frappe.show_alert({message: __(message.status), indicator: message.status === "Verified" ? "green" : "orange"});
                    frm.reload_doc();
                });
        }, __("Overtime"));
        frm.add_custom_button(__("Historial de conciliación"), () => frappe.set_route("List", "Overtime Reconciliation Run", {authorization: frm.doc.name}), __("Overtime"));
        if (enrolled) frm.add_custom_button(__("Elección y descanso del empleado"), () => {
            if (message.election) frappe.set_route("Form", "Overtime Settlement Election", message.election);
            else frappe.new_doc("Overtime Settlement Election", {authorization: frm.doc.name, choice: frm.doc.planned_settlement});
        }, __("Overtime"));
    });
};
