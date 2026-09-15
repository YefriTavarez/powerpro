frappe.provide("powerpro.checkin_overtime");
powerpro.checkin_overtime.render_rules_summary = (summary) => {
    if (!summary) return "";
    const e = value => frappe.utils.escape_html(String(value ?? ""));
    const p = summary.policy, h = summary.hours || {}, n = summary.night || {};
    if (!p) return `<p>${e(__("Falta una política aprobada para esta evaluación. No se presumen porcentajes de pago."))}</p>`;
    const number = (value, digits = 4) => value == null || !Number.isFinite(Number(value)) ? __("Sin cálculo") : Number(value).toFixed(digits);
    const percent = value => value == null ? __("Sin regla") : `${number(value, 2)}%`;
    const basis = {"Clock overlap": "Solo el tiempo trabajado entre 21:00 y 07:00",
        "Whole nocturnal session": "Toda la jornada cuando contiene al menos tres horas nocturnas"};
    const combined = {"Require review": "Requiere revisión", "Single highest premium": "Un solo recargo (el mayor)", "Additive premiums": "Sumar ambos recargos"};
    const rows = [
        [__("Extra ordinaria"), number(h.regular_35_hours), percent(p.regular_percent)],
        [__("Extra por encima del umbral semanal"), number(h.regular_100_hours), percent(p.extraordinary_percent)],
        [__("Feriado"), number(h.holiday_100_hours), percent(p.extraordinary_percent)],
        [__("Descanso semanal (efectivo)"), number(h.weekly_rest_hours), p.weekly_rest_cash ? percent(p.weekly_rest_percent) : __("Deshabilitado en estas reglas")],
        [__("Recargo nocturno sobre horas extra"), number(h.night_hours), percent(p.night_percent)],
        [__("Recargo nocturno sobre horas ordinarias"), number(n.ordinary_premium_hours), percent(p.night_percent)],
    ];
    return `<h5>${e(__("Reglas utilizadas en esta evaluación"))}</h5>
        <p>${e(__("Versión"))}: ${e(p.name)} · ${e(p.valid_from)} — ${e(p.valid_until)}</p>
        <p>${e(__("Nocturnidad"))}: ${e(__(basis[p.night_basis] || p.night_basis))}</p>
        <p>${e(__("Clasificación de la jornada"))}: ${e(__(n.classification || "Sin cálculo"))} · ${e(__("Horas entre 21:00 y 07:00"))}: ${e(number(n.clock_night_hours))}</p>
        <table class="table table-bordered"><thead><tr><th>${e(__("Concepto"))}</th><th>${e(__("Horas"))}</th><th>${e(__("Recargo sobre la hora base"))}</th></tr></thead>
        <tbody>${rows.map(row => `<tr>${row.map(value => `<td>${e(value)}</td>`).join("")}</tr>`).join("")}</tbody></table>
        <p>${e(__("El recargo nocturno se añade sobre la misma hora base. Las horas nocturnas pueden estar incluidas en las otras categorías; no se suman como horas adicionales."))}</p>
        <p>${e(__("Umbral semanal"))}: ${e(number(p.weekly_threshold))} · ${e(__("Evidencia semanal completa"))}: ${e(__(summary.weekly_evidence_complete === true ? "Sí" : "Pendiente"))}</p>
        <p>${e(__("Feriado coincidente con descanso semanal"))}: ${e(__(combined[p.holiday_weekly_rest_mode] || p.holiday_weekly_rest_mode))}</p>
        ${p.holiday_weekly_rest_compensatory ? `<p>${e(__("Habilitado: pago del feriado junto con descanso semanal compensatorio, sujeto a elección y cobertura salarial."))}</p>` : ""}
        <p>${e(__("Horas de feriado con base ya cubierta"))}: ${e(number(summary.holiday_base_covered_hours))}</p>
        <p>${e(__("Este detalle explica la vista previa. Los requisitos pendientes de evidencia, elección y liquidación siguen aplicando."))}</p>`;
};
powerpro.checkin_overtime.add_actions = (frm) => {
    powerpro.checkin_overtime.add_holiday_action(frm);
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

powerpro.checkin_overtime.add_holiday_action = (frm) => {
    if (frm.is_new() || frm.doc.docstatus === 2) return;
    const source = {source_type: frm.doc.doctype, source_name: frm.doc.name};
    const method = 'powerpro.controllers.overtime_holiday_base.';
    frappe.call({method: method + 'get_status', args: source}).then(({message: status}) => {
        if (!status?.can_declare) return;
        frm.add_custom_button(__('Base salarial del feriado'), () => {
            if (frm.is_dirty()) return frappe.msgprint(__('Guarde los cambios primero.'));
            frappe.prompt([
                {fieldname: 'covered_hours', fieldtype: 'Float', label: __('Horas de feriado con base ya incluida en el sueldo'),
                    default: status.coverage?.covered_hours ?? 0,
                    description: __('Indique cero si ninguna está cubierta. No incluya horas ajenas a esta conciliación.')},
                {fieldname: 'reference', fieldtype: 'Small Text', label: __('Referencia salarial y explicación de la cobertura'),
                    reqd: 1, default: status.coverage?.reference},
            ], values => {
                if (frm.is_dirty()) return frappe.msgprint(__('Guarde los cambios primero.'));
                frappe.call({method: method + 'preview', args: {...source, ...values}, freeze: true}).then(({message: p}) => {
                    const e = value => frappe.utils.escape_html(String(value ?? ''));
                    const estimate = p.estimate;
                    const html = `<p>${__('Horas de feriado')}: ${e(p.declaration.holiday_hours)}</p>
                        <p>${__('Horas con base cubierta')}: ${e(p.declaration.covered_hours)}</p>
                        <p>${e(p.declaration.reference)}</p>
                        ${estimate ? `<p>${__('Base ya incluida en el sueldo')}: ${e(estimate.holiday_base_already_in_salary)}</p>
                        <p>${__('Adicional estimado, sujeto a las demás validaciones')}: ${e(estimate.total_amount)}</p>` : ''}
                        <p>${__('Registrar esta declaración no aprueba las horas ni crea pagos. Después, procese o revise la conciliación.')}</p>`;
                    const dialog = new frappe.ui.Dialog({title: __('Cobertura salarial del feriado'),
                        fields: [{fieldname: 'preview', fieldtype: 'HTML', options: html}],
                        primary_action_label: __('Registrar cobertura'), primary_action() {
                            if (frm.is_dirty()) return frappe.msgprint(__('Guarde los cambios y obtenga otra vista previa.'));
                            frappe.call({method: method + 'apply', type: 'POST', freeze: true,
                                args: {...source, covered_hours: p.declaration.covered_hours,
                                    reference: p.declaration.reference, token: p.token}})
                                .then(() => {dialog.hide(); frm.reload_doc();});
                        }});
                    dialog.show();
                });
            }, __('Base salarial del feriado'), __('Vista previa'));
        }, __('Overtime'));
    });
};

powerpro.checkin_overtime.review = (frm, manual = false, observationWindow = null) => {
    if (frm.is_dirty()) {frappe.msgprint(__("Guarde los cambios antes de revisar.")); return;}
    const controller = frm.doc.docstatus === 2 ? "overtime_history" :
        (frm.doc.docstatus === 0 && frm.doc.doctype === "Retroactive Overtime Adjustment" ? "retroactive_draft_review" : "checkin_overtime_review");
    const fields = [{fieldname: "reason", label: __("Motivo y referencia de la corrección"), fieldtype: "Small Text", reqd: 1}];
    const scopedManual = manual && frm.doc.doctype === 'Retroactive Overtime Adjustment' && frm.doc.docstatus === 0;
    if (scopedManual) fields.push(
        {fieldname: 'authorized_interval_only', label: __('Aprobar solo el intervalo solicitado, conservando toda la jornada'), fieldtype: 'Check',
            description: __('Incluya toda la jornada y sus prolongaciones. El tiempo fuera del intervalo solicitado se conserva como evidencia y no se paga con este ajuste.')},
        {fieldname: 'observation_start', label: __('Inicio de la jornada completa'), fieldtype: 'Datetime',
            depends_on: 'eval:doc.authorized_interval_only', mandatory_depends_on: 'eval:doc.authorized_interval_only', default: observationWindow?.start},
        {fieldname: 'observation_end', label: __('Fin de la jornada completa'), fieldtype: 'Datetime',
            depends_on: 'eval:doc.authorized_interval_only', mandatory_depends_on: 'eval:doc.authorized_interval_only', default: observationWindow?.end,
            description: __('La ventana debe incluir el turno y el intervalo solicitado, no superar 24 horas y contener todos los intervalos trabajados. Las pausas se excluyen en la tabla.')});
    if (frm.doc.docstatus===2) fields.push(
        {fieldname:'expand_window',label:__('Ampliar ventana de observación histórica'),fieldtype:'Check'},
        {fieldname:'observation_start',label:__('Inicio de la jornada a revisar'),fieldtype:'Datetime',depends_on:'eval:doc.expand_window',default:observationWindow?.start},
        {fieldname:'observation_end',label:__('Fin de la jornada a revisar'),fieldtype:'Datetime',depends_on:'eval:doc.expand_window',default:observationWindow?.end,
            description:__('Debe conservar toda la jornada documentada y no superar 24 horas. No amplía la autorización ni genera pagos.')});
    if (manual) fields.push(
        {fieldname: "reference", fieldtype: "Small Text", label: __("Documento o referencia de la evidencia alternativa"), reqd: 1},
        {fieldname: "intervals", fieldtype: "Table", label: __("Toda la jornada trabajada, excluyendo pausas"), reqd: 1, in_place_edit: true,
            fields: [{fieldname: "start", label: __("Inicio"), fieldtype: "Datetime", in_list_view: 1, reqd: 1},
                     {fieldname: "end", label: __("Fin"), fieldtype: "Datetime", in_list_view: 1, reqd: 1}]},
        {fieldname: "full_session", label: __("Confirmo que estos intervalos incluyen toda la jornada y sus prolongaciones"), fieldtype: "Check", reqd: 1});
    frappe.prompt(fields, (values) => {
        if (frm.is_dirty()) {frappe.msgprint(__('Guarde los cambios antes de revisar.')); return;}
        const observation = frm.doc.docstatus===2 && values.expand_window ? JSON.stringify({start:values.observation_start,end:values.observation_end}) : undefined;
        const declaration = manual ? {full_session: Boolean(values.full_session), reference: values.reference,
            intervals: values.intervals.map(row => ({start: row.start, end: row.end}))} : undefined;
        if (scopedManual && values.authorized_interval_only) {
            declaration.review_scope = 'Authorized interval only';
            declaration.observation_window = {start: values.observation_start, end: values.observation_end};
        }
        frappe.call({method: `powerpro.controllers.${controller}.preview_review`, args: {authorization: frm.doc.name, source_type: frm.doc.doctype || "Overtime Authorization", reason: values.reason,
            manual_declaration: declaration && JSON.stringify(declaration),...(observation ? {observation_window:observation} : {})}, freeze: true}).then(({message: p}) => {
            const e = value => frappe.utils.escape_html(String(value ?? ""));
            const rows = [[__("Horas verificadas"), p.before.verified_hours || 0, p.after.verified_hours],
                [__("Entrada real"), p.before.actual_start, p.after.actual_start],
                [__("Salida real"), p.before.actual_end, p.after.actual_end],
                [__("Importe"), p.financial_before.settlement_amount || 0, p.historical_only ? __("Sin cambios") : (p.proposed_amount ?? __("Pendiente de liquidación"))]];
            if (p.historical_only) rows.unshift([__("Horas de la jornada completa"), p.worked_hours_before, p.worked_hours_after]);
            const html = `<p>${e(p.reason)}</p><table class="table table-bordered"><thead><tr><th></th><th>${__("Anterior")}</th><th>${__("Revisado")}</th></tr></thead><tbody>${rows.map(r => `<tr>${r.map(v => `<td>${e(v)}</td>`).join("")}</tr>`).join("")}</tbody></table>
                ${powerpro.checkin_overtime.render_rules_summary(p.rules_summary)}
                ${p.observation_window ? `<p>${__('Ventana de observación')}: ${e(p.observation_window.start)} — ${e(p.observation_window.end)}</p><p>${__('Horas fuera de autorización, sin nuevo pago')}: ${e(p.unapproved_hours)}</p>` : ''}
                ${p.manual_declaration ? `<p>${__("Fuente: jornada completa declarada por Gestión Humana. Las marcaciones originales se conservan como comparación.")}</p><p>${e(p.manual_declaration.reference)}</p>
                    <ul>${p.manual_declaration.intervals.map(row => `<li>${e(row.start)} — ${e(row.end)}</li>`).join("")}</ul>
                    <p>${__("Marcaciones originales")}</p><ul>${(p.checkin_comparison?.source_checkins || []).map(row => `<li>${e(row.name)}: ${e(row.time)} (${e(row.log_type)})</li>`).join("") || `<li>${__("Sin marcaciones disponibles")}</li>`}</ul>` : ""}
                <p>${p.draft_only ? __("Se registra la declaración y su evidencia. El ajuste sigue en borrador; su aprobación y liquidación requieren el flujo correspondiente.") : p.historical_only ? __("Se registra una revisión histórica sin reabrir el documento cancelado ni modificar su liquidación original.") : __("La aceptación conserva la evidencia anterior. Si hay liquidación previa, su reversión debe completarse antes de crear la sustitución.")}</p>
                <ul>${p.settlement_blockers.map(v => `<li>${e(v)}</li>`).join("")}${p.dependencies.map(v => `<li>${e(v.name)}: ${e(v.settlement_status)}</li>`).join("")}</ul>`;
            const dialog = new frappe.ui.Dialog({title: __("Revisión de evidencia"), fields: [{fieldname: "preview", fieldtype: "HTML", options: html}],
                primary_action_label: __("Aceptar revisión"), primary_action() {
                    if (frm.is_dirty()) {frappe.msgprint(__("Guarde los cambios y obtenga una vista previa nueva.")); return;}
                    frappe.call({method: `powerpro.controllers.${controller}.apply_review`, type: "POST",
                        args: {authorization: frm.doc.name, source_type: frm.doc.doctype || "Overtime Authorization", reason: p.reason, token: p.token,
                            manual_declaration: p.manual_declaration && JSON.stringify(p.manual_declaration),
                            ...(p.observation_window ? {observation_window:JSON.stringify(p.observation_window)} : {})}, freeze: true}).then(() => {dialog.hide();frm.reload_doc();});
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
        frm.add_custom_button(__('Revisar trabajo histórico'), () => powerpro.checkin_overtime.review(frm,false,status.observation_window), __('Overtime'));
        if (status.manual_review_allowed) frm.add_custom_button(__('Declarar jornada histórica'), () => powerpro.checkin_overtime.review(frm,true,status.observation_window), __('Overtime'));
    });
};
