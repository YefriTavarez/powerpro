frappe.provide("powerpro.checkin_overtime");
powerpro.checkin_overtime.add_actions = (frm) => {
    if (frm.doc.docstatus === 2) return powerpro.checkin_overtime.add_history_actions(frm);
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
        if (enrolled && message.manual_review_allowed) frm.add_custom_button(__("Declarar jornada de RR. HH."), () => powerpro.checkin_overtime.review(frm, true), __("Overtime"));
    });
};

powerpro.checkin_overtime.review = (frm, manual = false) => {
    if (frm.is_dirty()) {frappe.msgprint(__("Guarde los cambios antes de revisar.")); return;}
    const controller = frm.doc.docstatus === 2 ? "overtime_history" : "checkin_overtime_review";
    const fields = [{fieldname: "reason", label: __("Motivo y referencia de la corrección"), fieldtype: "Small Text", reqd: 1}];
    if (manual) fields.push(
        {fieldname: "reference", fieldtype: "Small Text", label: __("Documento o referencia de la evidencia alternativa"), reqd: 1},
        {fieldname: "intervals", fieldtype: "Table", label: __("Toda la jornada trabajada, excluyendo pausas"), reqd: 1, in_place_edit: true,
            fields: [{fieldname: "start", label: __("Inicio"), fieldtype: "Datetime", in_list_view: 1, reqd: 1},
                     {fieldname: "end", label: __("Fin"), fieldtype: "Datetime", in_list_view: 1, reqd: 1}]},
        {fieldname: "full_session", label: __("Confirmo que estos intervalos incluyen toda la jornada y sus prolongaciones"), fieldtype: "Check", reqd: 1});
    frappe.prompt(fields, (values) => {
        const declaration = manual ? {full_session: Boolean(values.full_session), reference: values.reference,
            intervals: values.intervals.map(row => ({start: row.start, end: row.end}))} : undefined;
        frappe.call({method: `powerpro.controllers.${controller}.preview_review`, args: {authorization: frm.doc.name, source_type: frm.doc.doctype || "Overtime Authorization", reason: values.reason,
            manual_declaration: declaration && JSON.stringify(declaration)}, freeze: true}).then(({message: p}) => {
            const e = value => frappe.utils.escape_html(String(value ?? ""));
            const rows = [[__("Horas verificadas"), p.before.verified_hours || 0, p.after.verified_hours],
                [__("Entrada real"), p.before.actual_start, p.after.actual_start],
                [__("Salida real"), p.before.actual_end, p.after.actual_end],
                [__("Importe"), p.financial_before.settlement_amount || 0, p.historical_only ? __("Sin cambios") : (p.proposed_amount ?? __("Pendiente de liquidación"))]];
            if (p.historical_only) rows.unshift([__("Horas de la jornada completa"), p.worked_hours_before, p.worked_hours_after]);
            const html = `<p>${e(p.reason)}</p><table class="table table-bordered"><thead><tr><th></th><th>${__("Anterior")}</th><th>${__("Revisado")}</th></tr></thead><tbody>${rows.map(r => `<tr>${r.map(v => `<td>${e(v)}</td>`).join("")}</tr>`).join("")}</tbody></table>
                ${p.manual_declaration ? `<p>${__("Fuente: jornada completa declarada por Gestión Humana. Las marcaciones originales se conservan como comparación.")}</p><p>${e(p.manual_declaration.reference)}</p>
                    <ul>${p.manual_declaration.intervals.map(row => `<li>${e(row.start)} — ${e(row.end)}</li>`).join("")}</ul>
                    <p>${__("Marcaciones originales")}</p><ul>${(p.checkin_comparison?.source_checkins || []).map(row => `<li>${e(row.name)}: ${e(row.time)} (${e(row.log_type)})</li>`).join("") || `<li>${__("Sin marcaciones disponibles")}</li>`}</ul>` : ""}
                <p>${p.historical_only ? __("Se registra una revisión histórica sin reabrir el documento cancelado ni modificar su liquidación original.") : __("La aceptación conserva la evidencia anterior. Si hay liquidación previa, su reversión debe completarse antes de crear la sustitución.")}</p>
                <ul>${p.settlement_blockers.map(v => `<li>${e(v)}</li>`).join("")}${p.dependencies.map(v => `<li>${e(v.name)}: ${e(v.settlement_status)}</li>`).join("")}</ul>`;
            const dialog = new frappe.ui.Dialog({title: __("Revisión de evidencia"), fields: [{fieldname: "preview", fieldtype: "HTML", options: html}],
                primary_action_label: __("Aceptar revisión"), primary_action() {
                    if (frm.is_dirty()) {frappe.msgprint(__("Guarde los cambios y obtenga una vista previa nueva.")); return;}
                    frappe.call({method: `powerpro.controllers.${controller}.apply_review`, type: "POST",
                        args: {authorization: frm.doc.name, source_type: frm.doc.doctype || "Overtime Authorization", reason: p.reason, token: p.token,
                            manual_declaration: p.manual_declaration && JSON.stringify(p.manual_declaration)}, freeze: true}).then(() => {dialog.hide();frm.reload_doc();});
                }});
            dialog.show();
        });
    }, __("Revisar evidencia corregida"), __("Vista previa"));
};


powerpro.checkin_overtime.add_history_actions = (frm) => {
    if (frm.doc.docstatus !== 2) return;
    frappe.call({method: 'powerpro.controllers.overtime_history.get_status',
        args: {authorization: frm.doc.name, source_type: frm.doc.doctype}}).then(({message: status}) => {
        if (!status?.applicable) return;
        const filter = frm.doc.doctype === 'Retroactive Overtime Adjustment' ? {retroactive_adjustment: frm.doc.name} : {authorization: frm.doc.name};
        frm.add_custom_button(__('Historial de evidencia física'), () => frappe.set_route('List', 'Overtime Reconciliation Run', filter), __('Overtime'));
        if (!status.can_review) return;
        frm.add_custom_button(__('Revisar trabajo histórico'), () => powerpro.checkin_overtime.review(frm), __('Overtime'));
        if (status.manual_review_allowed) frm.add_custom_button(__('Declarar jornada histórica'), () => powerpro.checkin_overtime.review(frm, true), __('Overtime'));
    });
};
