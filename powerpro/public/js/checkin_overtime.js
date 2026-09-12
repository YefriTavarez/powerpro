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
        if (enrolled && message.can_night) frm.add_custom_button(__("Nocturnidad ordinaria"), () => {
            if (frm.is_dirty()) {frappe.msgprint(__("Guarde los cambios antes de continuar.")); return;}
            if (message.ordinary_night) frappe.set_route("Form", "Ordinary Night Settlement", message.ordinary_night);
            else frappe.new_doc("Ordinary Night Settlement", {employee: frm.doc.employee, work_date: frm.doc.work_date,
                settlement_payroll_date: frm.doc.auto_payroll_date || frm.doc.work_date});
        }, __("Overtime"));
        if (enrolled) frm.add_custom_button(__("Revisar evidencia corregida"), () => powerpro.checkin_overtime.review(frm), __("Overtime"));
    });
};

powerpro.checkin_overtime.review = (frm) => {
    if (frm.is_dirty()) {frappe.msgprint(__("Guarde los cambios antes de revisar.")); return;}
    frappe.prompt([{fieldname: "reason", label: __("Motivo y referencia de la corrección"), fieldtype: "Small Text", reqd: 1}], ({reason}) => {
        frappe.call({method: "powerpro.controllers.checkin_overtime_review.preview_review", args: {authorization: frm.doc.name, reason}, freeze: true}).then(({message: p}) => {
            const e = value => frappe.utils.escape_html(String(value ?? ""));
            const rows = [[__("Horas verificadas"), p.before.verified_hours || 0, p.after.verified_hours],
                [__("Entrada real"), p.before.actual_start, p.after.actual_start],
                [__("Salida real"), p.before.actual_end, p.after.actual_end],
                [__("Importe"), p.financial_before.settlement_amount || 0, p.proposed_amount ?? __("Pendiente de liquidación")]];
            const html = `<p>${e(p.reason)}</p><table class="table table-bordered"><thead><tr><th></th><th>${__("Anterior")}</th><th>${__("Revisado")}</th></tr></thead><tbody>${rows.map(r => `<tr>${r.map(v => `<td>${e(v)}</td>`).join("")}</tr>`).join("")}</tbody></table>
                <p>${__("La aceptación conserva la evidencia anterior. Si hay liquidación previa, su reversión debe completarse antes de crear la sustitución.")}</p>
                <ul>${p.settlement_blockers.map(v => `<li>${e(v)}</li>`).join("")}${p.dependencies.map(v => `<li>${e(v.name)}: ${e(v.settlement_status)}</li>`).join("")}</ul>`;
            const dialog = new frappe.ui.Dialog({title: __("Revisión de evidencia"), fields: [{fieldname: "preview", fieldtype: "HTML", options: html}],
                primary_action_label: __("Aceptar revisión"), primary_action() {
                    if (frm.is_dirty()) {frappe.msgprint(__("Guarde los cambios y obtenga una vista previa nueva.")); return;}
                    frappe.call({method: "powerpro.controllers.checkin_overtime_review.apply_review", type: "POST",
                        args: {authorization: frm.doc.name, reason: p.reason, token: p.token}, freeze: true}).then(() => {dialog.hide();frm.reload_doc();});
                }});
            dialog.show();
        });
    }, __("Revisar evidencia corregida"), __("Vista previa"));
};
