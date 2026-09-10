/* Daily meal allowances: all manager operations stay on the Work Call. */
frappe.provide('powerpro.dietas');
(() => {
    const api = 'powerpro.dietas.service.';
    const accounting = 'powerpro.dietas.accounting.';
    const esc = (value) => frappe.utils.escape_html(String(value ?? ''));
    const labels = {None: 'Sin solicitud', Pending: 'Pendiente', Approved: 'Aprobada', Rejected: 'Rechazada',
        Cancelled: 'Cancelada', Unpaid: 'Pendiente de pago', Paid: 'Pagada', Disabled: 'Deshabilitada',
        Draft: 'Borrador', Posted: 'Contabilizada', Error: 'Contabilidad pendiente', Confirmed: 'Confirmado', Reversed: 'Corregido'};
    const label = value => labels[value] || value;
    const auditHtml = events => {
        const actions = {request:'Solicitud creada',approve:'Aprobada',reject:'Rechazada',amount:'Monto ajustado',
            reconsider:'Devuelta a pendiente',approve_and_pay:'Aprobada y pagada',confirm_payment:'Pago confirmado',
            journal_draft:'Borrador contable generado',journal_status:'Estado contable actualizado',
            authorization_cancelled:'Autorización cancelada',attendance_review:'Revisión de asistencia',
            reverse_erroneous_payment:'Registro de pago corregido'};
        return '<ul>' + (events || []).map(e => `<li><strong>${esc(actions[e.action] || e.action)}</strong> · ${esc(e.at)} · ${esc(e.user)}
            ${e.amount != null ? `<br>Monto: ${esc(e.amount)}` : ''}${e.previous_amount != null ? ` · Anterior: ${esc(e.previous_amount)}` : ''}
            ${e.reason ? `<br>${esc(e.reason)}` : ''}</li>`).join('') + '</ul>';
    };
    const call = (method, args) => frappe.call({method, args, type: 'POST'}).then(r => r.message);
    const amount = (value, currency) => format_currency(value, currency);
    const batchLink = name => `<a href="/app/lote-de-pago-de-dietas/${encodeURIComponent(name)}">${esc(name)}</a>`;
    const selectedDate = dates => dates.includes(frappe.datetime.get_today()) ? frappe.datetime.get_today() : dates.length === 1 ? dates[0] : '';

    function summary(frm, data) {
        frm.dashboard.parent.find('.dieta-summary').remove();
        if (!data?.enabled) return;
        const s = data.summary;
        frm.dashboard.add_section(
            `<strong>Dietas</strong> · ${s.pending} pendientes · Aprobadas sin pagar: ${amount(s.approved_unpaid, data.currency)} · ` +
            `Pagado: ${amount(s.paid, data.currency)} · Contabilidad por revisar: ${s.accounting_attention}` +
            '<div class="mt-3"><button type="button" class="btn btn-sm btn-default dieta-view-payments">Ver pagos de dietas</button></div>',
            null, 'custom dieta-summary'
        );
        frm.dashboard.parent.find('.dieta-view-payments').on('click', () => openHistory(frm));
        frm.dashboard.show();
    }
    async function refresh(frm) {
        if (frm.doc.docstatus === 0) return;
        const data = await call(api + 'work_call_context', {work_call: frm.doc.name});
        if (frm.doc.name !== data?.work_call && data?.work_call) return;
        if (!data?.enabled) { summary(frm, data); return; }
        if (data.active) {
            frm.add_custom_button('Pagar dietas', () => openWorkers(frm, data, true), 'Dietas');
            frm.add_custom_button('Gestionar solicitudes', () => openWorkers(frm, data, false), 'Dietas');
        }
        frm.add_custom_button('Ver pagos', () => openHistory(frm), 'Dietas');
        summary(frm, data);
    }

    function openWorkers(frm, context, paying) {
        let rows = [], generation = 0, dialog;
        let requiresCenters = paying && Boolean(context.generate_journal_entry);
        let company = context.company;
        const fields = [
            {fieldname: 'work_date', fieldtype: 'Select', label: 'Fecha de trabajo', options: [''].concat(context.dates),
                default: selectedDate(context.dates), reqd: 1, onchange: () => load()},
            {fieldname: 'workers', fieldtype: 'HTML'},
            {fieldname: 'bulk_amount', fieldtype: 'Currency', label: 'Monto para seleccionados'},
            {fieldname: 'reason', fieldtype: 'Small Text', label: 'Motivo del cambio / acción'},
            {fieldname: 'apply_amount', fieldtype: 'Button', label: 'Aplicar monto a seleccionados', click: () => {
                const value = Number(dialog.get_value('bulk_amount'));
                if (!Number.isFinite(value) || value <= 0) return frappe.msgprint('Indique un monto positivo.');
                chosen().forEach(r => { r.amount = value; }); render();
            }},
        ];
        if (paying) fields.push(
            {fieldname: 'payment_date', fieldtype: 'Date', label: 'Fecha real del pago', default: frappe.datetime.get_today(), reqd: 1},
            {fieldname: 'mode_of_payment', fieldtype: 'Select', label: 'Método de pago', options: [''].concat(context.methods), reqd: 1},
            {fieldname: 'reference', fieldtype: 'Data', label: 'Referencia del pago'},
            {fieldname: 'evidence', fieldtype: 'Attach', label: 'Comprobante (opcional)'},
        );
        else fields.push({fieldname: 'action', fieldtype: 'Select', label: 'Acción',
            options: [{value: 'approve', label: 'Aprobar'}, {value: 'reject', label: 'Rechazar'},
                {value: 'amount', label: 'Cambiar monto'}, {value: 'reconsider', label: 'Reconsiderar / volver a pendiente'}], reqd: 1});
        fields.push({fieldname: 'result', fieldtype: 'HTML'});
        dialog = new frappe.ui.Dialog({title: paying ? 'Pagar dietas' : 'Gestionar solicitudes de dieta',
            size: 'extra-large', fields, primary_action_label: paying ? 'Procesar pagos' : 'Aplicar acción',
            primary_action: async values => {
                const selection = chosen().map(r => ({employee: r.employee, amount: r.amount, version: r.version, cost_center: requiresCenters ? r.cost_center || '' : null, reason: values.reason || ''}));
                if (!selection.length) return frappe.msgprint('Seleccione al menos un empleado.');
                const missing = requiresCenters ? chosen().filter(r => !r.cost_center) : [];
                if (missing.length) return frappe.msgprint('Seleccione un centro de costo para: ' + missing.map(r => esc(r.employee_name)).join(', '));
                dialog.disable_primary_action();
                try {
                    const args = {work_call: frm.doc.name, work_date: values.work_date, rows: selection};
                    if (paying) {
                        Object.assign(args, {payment_date: values.payment_date, mode_of_payment: values.mode_of_payment,
                            reference: values.reference || '', evidence: values.evidence || ''});
                        const preview = await call(api + 'preview_payout', args);
                        const result = await confirmPayment(preview, args);
                        if (!result) return; // User returned to the selection without confirming.
                        dialog.hide();
                        const accountingMessage = {
                            Pending: 'El pago quedó registrado. La contabilidad está pendiente de procesamiento.',
                            Error: 'El pago quedó registrado, pero la contabilidad requiere revisión. No vuelva a registrar el pago.',
                            Disabled: 'La generación del asiento contable está deshabilitada.',
                            Draft: 'Se generó un borrador contable; está pendiente de envío.',
                            Posted: 'El asiento contable está enviado.',
                            Cancelled: 'El asiento contable está cancelado; revise el lote.',
                        }[result.accounting_status] || `Contabilidad: ${label(result.accounting_status)}.`;
                        frappe.msgprint({
                            title: result.status === 'Confirmed' ? 'Pago registrado correctamente' : 'Registro de pago recuperado',
                            indicator: result.status === 'Confirmed' ? 'green' : 'orange',
                            message: `<p>Lote: ${batchLink(result.batch)}</p><p>Estado del pago: ${esc(label(result.status))}.</p><p>${esc(accountingMessage)}</p>`,
                        });
                        try { await refreshSummary(frm); }
                        catch (error) {
                            console.error('Pago registrado; no se pudo actualizar el resumen:', error);
                            frappe.show_alert({message: 'El pago ya está registrado. Recargue la convocatoria para actualizar el resumen.', indicator: 'orange'});
                        }
                    } else {
                        await call(api + 'manage_requests', {...args, action: values.action, reason: values.reason || ''});
                        dialog.fields_dict.result.$wrapper.text('Solicitudes actualizadas.');
                        await load(); await refreshSummary(frm);
                    }
                } catch (error) {
                    console.error('No se pudo completar la acción de Dietas:', error);
                    dialog.fields_dict.result.$wrapper.html('<p class="text-danger" role="alert">No se pudo completar la acción. Revise el mensaje de error y los datos antes de volver a intentar.</p>');
                } finally { dialog.enable_primary_action(); }
            }});
        const chosen = () => rows.filter(r => r.selected && !r.disabled);
        const total = () => dialog.fields_dict.workers.$wrapper.find('.dieta-total').html(
            `${chosen().length} seleccionados · Total: <strong>${amount(chosen().reduce((s, r) => s + Number(r.amount || 0), 0), context.currency)}</strong>`);
        function render() {
            const wrapper = dialog.fields_dict.workers.$wrapper;
            wrapper.html(`<div class="table-responsive"><table class="table table-bordered"><thead><tr>
                <th><input type="checkbox" class="select-all" aria-label="Seleccionar empleados elegibles"></th>
                <th>Empleado</th><th>Monto</th>${requiresCenters ? '<th>Centro de costo</th>' : ''}<th>Solicitud</th><th>Pago</th><th>Detalle</th></tr></thead><tbody>` +
                rows.map((r, i) => `<tr><td><input type="checkbox" data-index="${i}" class="pick" aria-label="Seleccionar ${esc(r.employee_name)}" ${r.selected ? 'checked' : ''} ${r.disabled ? 'disabled' : ''}></td>
                    <td>${esc(r.employee_name)}<br><small>${esc(r.employee)}</small></td>
                    <td><input type="number" min="0.01" step="0.01" class="form-control dieta-amount" data-index="${i}" aria-label="Monto ${esc(r.employee_name)}" value="${esc(r.amount)}" ${r.disabled ? 'disabled' : ''}></td>
                    ${requiresCenters ? `<td><div class="dieta-cost-center" data-index="${i}"></div></td>` : ''}
                    <td>${esc(label(r.approval_status))}${r.review_required ? '<br><span class="text-danger">Requiere revisión</span>' : ''}</td>
                    <td>${esc(label(r.payment_status))}</td><td><button type="button" class="btn btn-xs btn-default detail" data-index="${i}">Ver detalle</button></td></tr>`).join('') +
                `</tbody></table></div><p class="dieta-total"></p><p class="text-muted">${paying ? 'La confirmación aprueba los montos e indica que el dinero ya fue entregado o transferido.' : 'Para modificar una dieta aprobada, vuelva a pendiente y apruébela nuevamente.'}</p>`);
            if (requiresCenters) wrapper.find('.dieta-cost-center').each(function () {
                const r = rows[Number(this.dataset.index)];
                const control = frappe.ui.form.make_control({parent: this, render_input: true,
                    df: {fieldname: 'cost_center', fieldtype: 'Link', options: 'Cost Center',
                        label: `Centro de costo: ${r.employee_name}`, only_select: true,
                        read_only: r.disabled ? 1 : 0,
                        get_query: () => ({filters: {company, is_group: 0, disabled: 0}}),
                        onchange: () => { r.cost_center = control.get_value() || ''; }}});
                control.set_value(r.cost_center || '');
            });
            wrapper.find('.pick').on('change', function () { rows[Number(this.dataset.index)].selected = this.checked; total(); });
            wrapper.find('.select-all').on('change', function () { rows.forEach(r => { r.selected = !r.disabled && this.checked; }); render(); });
            wrapper.find('.dieta-amount').on('input', function () { rows[Number(this.dataset.index)].amount = Number(this.value); total(); });
            wrapper.find('.detail').on('click', function () {
                const r = rows[Number(this.dataset.index)];
                const details = new frappe.ui.Dialog({title: r.employee_name, fields: [{fieldname: 'detail', fieldtype: 'HTML'}]});
                details.fields_dict.detail.$wrapper.html(`<p>${esc(r.start)} — ${esc(r.end)}</p><p>${esc(r.notes)}</p><p>${esc(r.review_reason)}</p>`);
                details.fields_dict.detail.$wrapper.append(auditHtml(r.audit));
                details.show();
            }); total();
        }
        async function load() {
            if (!dialog) return;
            const current = ++generation;
            const date = dialog.get_value('work_date');
            rows = []; render();
            if (!date) return;
            const result = await call(api + 'work_call_context', {work_call: frm.doc.name, work_date: date});
            if (current !== generation) return;
            requiresCenters = paying && Boolean(result.generate_journal_entry);
            company = result.company;
            rows = (result.rows || []).filter(r => paying || r.request).map(r => ({...r, selected: false,
                disabled: r.payment_status === 'Paid' || (paying && (['Rejected', 'Cancelled'].includes(r.approval_status) || r.source_work_call !== frm.doc.name))}));
            render();
        }
        dialog.show(); load();
    }

    function confirmPayment(preview, args) {
        // Reuse the exact key and payload after an uncertain response; never create a second payment.
        const payload = {...args, token: preview.token, idempotency_key: crypto.randomUUID()};
        return new Promise(resolve => {
            let submitting = false, result = null;
            const confirm = new frappe.ui.Dialog({title: 'Confirmar pagos realizados', size: 'large', static: true,
                fields: [{fieldname: 'preview', fieldtype: 'HTML'}, {fieldname: 'feedback', fieldtype: 'HTML'}],
                primary_action_label: 'Confirmar pagos realizados',
                secondary_action_label: 'Volver',
                secondary_action: () => { if (!submitting) confirm.hide(); },
                onhide: () => resolve(result),
                primary_action: async () => {
                    if (submitting) return;
                    submitting = true;
                    confirm.disable_primary_action();
                    confirm.get_primary_btn().text('Registrando pago…');
                    confirm.fields_dict.feedback.$wrapper.html('<p role="status">Registrando el pago. Espere la confirmación…</p>');
                    try {
                        const response = await call(api + 'confirm_payout', payload);
                        if (!response?.batch) throw new Error('No se recibió la confirmación del lote.');
                        result = response;
                        confirm.hide();
                    } catch (error) {
                        console.error('No se pudo confirmar el resultado del pago:', error);
                        confirm.fields_dict.feedback.$wrapper.html('<p class="text-danger" role="alert">No se pudo confirmar el resultado. Si hubo un error de conexión, reintente desde este mismo diálogo: se verificará el mismo pago para evitar duplicados. Si el servidor indicó un error de validación, pulse Volver y corrija los datos.</p>');
                    } finally {
                        submitting = false;
                        confirm.enable_primary_action();
                        confirm.get_primary_btn().text('Confirmar pagos realizados');
                    }
                }});
            confirm.fields_dict.preview.$wrapper.html(paymentPreviewHtml(preview));
            confirm.show();
        });
    }
    function paymentPreviewHtml(preview) {
        const showCenters = Boolean(preview.generate_journal_entry);
        const money = value => amount(value, preview.currency);
        const subtotals = new Map();
        if (showCenters) preview.rows.forEach(row => {
            subtotals.set(row.cost_center, (subtotals.get(row.cost_center) || 0) + Number(row.amount));
        });
        const distribution = showCenters && subtotals.size ? `
            <h5 class="mt-4 mb-3">Distribución por centro de costo</h5>
            <div class="table-responsive">
                <table class="table table-bordered table-sm">
                    <caption class="sr-only">Resumen de importes por centro de costo</caption>
                    <thead><tr><th scope="col">Centro de costo</th><th scope="col" class="text-right">Subtotal</th></tr></thead>
                    <tbody>${[...subtotals].map(([center, total]) => `
                        <tr><th scope="row" class="dieta-preview-name">${esc(center)}</th>
                            <td class="dieta-preview-money text-right">${money(total)}</td></tr>`).join('')}</tbody>
                </table>
            </div>` : '';
        return `<div class="dieta-payment-preview">
            <style>
                .dieta-payment-preview .dieta-preview-money { white-space: nowrap; font-variant-numeric: tabular-nums; }
                .dieta-payment-preview .dieta-preview-name { font-weight: normal; }
                .dieta-payment-preview th, .dieta-payment-preview td { vertical-align: middle; padding: 10px 12px; }
                .dieta-payment-preview thead, .dieta-payment-preview tfoot { background: var(--subtle-fg, #f5f7fa); }
                .dieta-payment-preview .dieta-preview-meta { background: var(--subtle-fg, #f5f7fa); border-radius: 8px; padding: 12px 16px; }
                .dieta-payment-preview .dieta-preview-meta strong { display: block; overflow-wrap: anywhere; }
            </style>
            <div class="dieta-preview-meta mb-4">
                <div class="row">
                    <div class="col-sm-6 mb-2"><span class="text-muted">Fecha real del pago</span>
                        <strong>${esc(frappe.datetime.str_to_user(preview.payment.payment_date))}</strong></div>
                    <div class="col-sm-6 mb-2"><span class="text-muted">Método de pago</span>
                        <strong>${esc(preview.payment.mode_of_payment)}</strong></div>
                </div>
            </div>
            <h5 class="mb-3">Detalle de pagos <span class="text-muted">· ${preview.rows.length} empleados</span></h5>
            <div class="table-responsive">
                <table class="table table-bordered table-sm">
                    <caption class="sr-only">Dietas por empleado</caption>
                    <thead><tr><th scope="col">Empleado</th>${showCenters ? '<th scope="col">Centro de costo</th>' : ''}
                        <th scope="col" class="text-right">Monto</th></tr></thead>
                    <tbody>${preview.rows.map(row => `
                        <tr><th scope="row" class="dieta-preview-name">${esc(row.employee_name)}</th>
                            ${showCenters ? `<td>${esc(row.cost_center)}</td>` : ''}
                            <td class="dieta-preview-money text-right">${money(row.amount)}</td></tr>`).join('')}</tbody>
                    <tfoot><tr><th scope="row" colspan="${showCenters ? 2 : 1}">Total a registrar</th>
                        <td class="dieta-preview-money text-right"><strong>${money(preview.total)}</strong></td></tr></tfoot>
                </table>
            </div>
            ${distribution}
            <p class="text-muted mt-3 mb-0">Al confirmar, se aprobarán estos montos y se registrará el dinero como entregado.
                Esta acción no realiza transferencias bancarias.</p>
        </div>`;
    }
    async function refreshSummary(frm) {
        summary(frm, await call(api + 'work_call_context', {work_call: frm.doc.name}));
    }
    async function openHistory(frm) {
        const dialog = new frappe.ui.Dialog({title: 'Pagos de dietas', size: 'extra-large', fields: [{fieldname: 'history', fieldtype: 'HTML'}]});
        async function load() {
            const batches = await call(api + 'payment_history', {work_call: frm.doc.name});
            const wrapper = dialog.fields_dict.history.$wrapper;
            wrapper.html(batches.length ? batches.map((b, i) => `<details class="well"><summary><strong>${esc(b.name)}</strong> · ${esc(b.payment_date)} · ${esc(b.mode_of_payment)} · ${amount(b.total, b.currency)} · ${esc(label(b.status))}</summary>
                <p>Abrir lote: ${batchLink(b.name)}</p><p>Fecha de trabajo: ${esc(b.work_date)} · Registrado por: ${esc(b.paid_by)} · ${esc(b.paid_on)}</p>
                <p>Referencia: ${esc(b.reference)} · Contabilidad: ${esc(label(b.accounting_status))}</p>
                <p>${esc(b.accounting_error)}</p><p>Comprobante: ${esc(b.evidence || "Sin adjunto")}</p><ul>${b.rows.map(r => `<li>${esc(r.employee_name)}: ${esc(r.amount)}${r.cost_center ? ` · ${esc(r.cost_center)}` : ''}</li>`).join('')}</ul>
                ${['Pending', 'Error'].includes(b.accounting_status) && b.status === 'Confirmed' ? `<button class="btn btn-sm btn-default retry" data-index="${i}">Reintentar contabilidad</button>` : ''}
                ${frappe.user.has_role('HR Manager') && b.status === 'Confirmed' ? `<button class="btn btn-sm btn-default reverse" data-index="${i}">Corregir registro erróneo</button>` : ''}
                ${auditHtml(b.audit)}</details>`).join('') : '<p>No hay pagos registrados.</p>');
            wrapper.find('.retry').on('click', async function () {
                this.disabled = true;
                try { await call(accounting + 'retry_accounting', {batch_name: batches[Number(this.dataset.index)].name});
                    frappe.show_alert('Contabilidad en cola.'); } finally { this.disabled = false; }
            });
            wrapper.find('.reverse').on('click', function () {
                const batch = batches[Number(this.dataset.index)];
                frappe.prompt([{fieldname: 'reason', fieldtype: 'Small Text', label: 'Motivo: el pago fue registrado por error; esto no registra una devolución', reqd: 1}], async values => {
                    await call(accounting + 'reverse_erroneous_payout', {batch_name: batch.name, reason: values.reason});
                    await load(); await refreshSummary(frm);
                }, 'Corregir registro erróneo', 'Confirmar corrección');
            });
        }
        dialog.add_custom_action('Actualizar', load); dialog.show(); await load();
    }
    powerpro.dietas.refresh = refresh;
    powerpro.dietas.openWorkers = openWorkers;
    powerpro.dietas.openHistory = openHistory;
    frappe.ui.form.on('Overtime Work Call', {refresh: frm => refresh(frm).catch(error => {
        console.error('No se pudo cargar Dietas:', error);
        frappe.show_alert({message: 'No se pudo cargar Dietas. Recargue la convocatoria; si persiste, contacte a soporte.', indicator: 'red'});
    })});
})();
