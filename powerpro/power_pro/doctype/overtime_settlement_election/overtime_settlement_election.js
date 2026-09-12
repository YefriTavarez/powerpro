frappe.ui.form.on("Overtime Settlement Election", {
    refresh(frm) {
        if (frm.is_new()) return;
        const act = (method, args = {}) => {
            if (frm.is_dirty()) { frappe.msgprint(__("Guarde los cambios primero.")); return; }
            return frappe.call({method: `powerpro.controllers.overtime_rest.${method}`, type: "POST",
                args: {name: frm.doc.name, ...args}, freeze: true}).then(() => frm.reload_doc());
        };
        const ask = (title, fields, method) => {
            const d = new frappe.ui.Dialog({title: __(title), fields, primary_action_label: __("Confirmar"),
                primary_action(values) { act(method, values)?.then(() => d.hide()); }});
            d.show();
        };
        const reason = [{fieldname: "reason", label: __("Motivo"), fieldtype: "Small Text", reqd: 1}];
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__("Confirmar elección del empleado"), () => act("approve_election"));
            return;
        }
        if (frm.doc.docstatus !== 1) return;
        frappe.call({method: "powerpro.controllers.overtime_rest.get_rest_status", args: {name: frm.doc.name}})
            .then(({message}) => {
                if (message.status === "Overdue") frm.dashboard.set_headline_alert(__("El descanso está vencido y requiere revisión de Gestión Humana."), "orange");
                if (message.status === "Review") frm.dashboard.set_headline_alert(__("Hay nuevas marcaciones que contradicen el disfrute confirmado. Revise su evidencia."), "orange");
            });
        frm.add_custom_button(__("Cancelar elección"), () => ask("Cancelar elección", reason, "cancel_election"));
        if (frm.doc.choice !== "Compensatory Rest") return;
        if (frm.doc.status === "Enjoyed") {
            frm.add_custom_button(__("Corregir confirmación de disfrute"), () => ask("Corregir confirmación", reason, "revoke_enjoyment"));
            return;
        }
        frm.add_custom_button(__("Vincular licencia aprobada"), () => ask("Vincular licencia", [
            {fieldname: "leave_application", label: __("Licencia aprobada"), fieldtype: "Link", options: "Leave Application", reqd: 1,
                get_query: () => ({filters: {employee: frm.doc.employee, docstatus: 1, status: "Approved"}})}
        ], "link_leave"));
        frm.add_custom_button(__("Reprogramar descanso"), () => ask("Reprogramar descanso", [
            {fieldname: "start", label: __("Inicio"), fieldtype: "Datetime", default: frm.doc.planned_start, reqd: 1},
            {fieldname: "end", label: __("Fin"), fieldtype: "Datetime", default: frm.doc.planned_end, reqd: 1}, ...reason
        ], "reschedule"));
        frm.add_custom_button(__("Confirmar descanso disfrutado"), () => ask("Confirmar disfrute", [
            {fieldname: "actual_start", label: __("Inicio real"), fieldtype: "Datetime", default: frm.doc.planned_start, reqd: 1},
            {fieldname: "actual_end", label: __("Fin real"), fieldtype: "Datetime", default: frm.doc.planned_end, reqd: 1},
            {fieldname: "reference", label: __("Evidencia de verificación con el empleado"), fieldtype: "Small Text", reqd: 1}
        ], "confirm_enjoyment"));
    }
});
