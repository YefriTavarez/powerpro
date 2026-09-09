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
    const selectedDate = dates => dates.includes(frappe.datetime.get_today()) ? frappe.datetime.get_today() : dates.length === 1 ? dates[0] : '';

    function summary(frm, data) {
        frm.dashboard.wrapper.find('.dieta-summary').remove();
        if (!data?.enabled) return;
        const s = data.summary;
        $('<div class="dieta-summary alert alert-info"></div>').html(
            `<strong>Dietas</strong> · ${s.pending} pendientes · Aprobadas sin pagar: ${amount(s.approved_unpaid, data.currency)} · ` +
            `Pagado: ${amount(s.paid, data.currency)} · Contabilidad por revisar: ${s.accounting_attention}`
        ).appendTo(frm.dashboard.wrapper);
    }
    async function refresh(frm) {
        if (frm.doc.docstatus === 0) return;
        const data = await call(api + 'work_call_context', {work_call: frm.doc.name});
        if (frm.doc.name !== data?.work_call && data?.work_call) return;
        summary(frm, data);
        if (!data?.enabled) return;
        if (data.active) {
            frm.add_custom_button('Pagar dietas', () => openWorkers(frm, data, true), 'Dietas');
            frm.add_custom_button('Gestionar solicitudes', () => openWorkers(frm, data, false), 'Dietas');
        }
        frm.add_custom_button('Ver pagos', () => openHistory(frm), 'Dietas');
    }

    function openWorkers(frm, context, paying) {
        let rows = [], generation = 0, dialog;
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
            size: 'extra-large', fields, primary_action_label: paying ? 'Revisar pagos' : 'Aplicar acción',
            primary_action: async values => {
                const selection = chosen().map(r => ({employee: r.employee, amount: r.amount, version: r.version, reason: values.reason || ''}));
                if (!selection.length) return frappe.msgprint('Seleccione al menos un empleado.');
                dialog.disable_primary_action();
                try {
                    const args = {work_call: frm.doc.name, work_date: values.work_date, rows: selection};
                    if (paying) {
                        Object.assign(args, {payment_date: values.payment_date, mode_of_payment: values.mode_of_payment,
                            reference: values.reference || '', evidence: values.evidence || ''});
                        const preview = await call(api + 'preview_payout', args);
                        confirmPayment(preview, args, async result => {
                            dialog.fields_dict.result.$wrapper.text(`Pago registrado: ${result.batch}. Contabilidad: ${label(result.accounting_status)}.`);
                            await load(); await refreshSummary(frm);
                        });
                    } else {
                        await call(api + 'manage_requests', {...args, action: values.action, reason: values.reason || ''});
                        dialog.fields_dict.result.$wrapper.text('Solicitudes actualizadas.');
                        await load(); await refreshSummary(frm);
                    }
                } finally { dialog.enable_primary_action(); }
            }});
        const chosen = () => rows.filter(r => r.selected && !r.disabled);
        const total = () => dialog.fields_dict.workers.$wrapper.find('.dieta-total').html(
            `${chosen().length} seleccionados · Total: <strong>${amount(chosen().reduce((s, r) => s + Number(r.amount || 0), 0), context.currency)}</strong>`);
        function render() {
            const wrapper = dialog.fields_dict.workers.$wrapper;
            wrapper.html(`<div class="table-responsive"><table class="table table-bordered"><thead><tr>
                <th><input type="checkbox" class="select-all" aria-label="Seleccionar empleados elegibles"></th>
                <th>Empleado</th><th>Monto</th><th>Solicitud</th><th>Pago</th><th>Detalle</th></tr></thead><tbody>` +
                rows.map((r, i) => `<tr><td><input type="checkbox" data-index="${i}" class="pick" aria-label="Seleccionar ${esc(r.employee_name)}" ${r.selected ? 'checked' : ''} ${r.disabled ? 'disabled' : ''}></td>
                    <td>${esc(r.employee_name)}<br><small>${esc(r.employee)}</small></td>
                    <td><input type="number" min="0.01" step="0.01" class="form-control dieta-amount" data-index="${i}" aria-label="Monto ${esc(r.employee_name)}" value="${esc(r.amount)}" ${r.disabled ? 'disabled' : ''}></td>
                    <td>${esc(label(r.approval_status))}${r.review_required ? '<br><span class="text-danger">Requiere revisión</span>' : ''}</td>
                    <td>${esc(label(r.payment_status))}</td><td><button type="button" class="btn btn-xs btn-default detail" data-index="${i}">Ver detalle</button></td></tr>`).join('') +
                `</tbody></table></div><p class="dieta-total"></p><p class="text-muted">${paying ? 'La confirmación aprueba los montos e indica que el dinero ya fue entregado o transferido.' : 'Para modificar una dieta aprobada, vuelva a pendiente y apruébela nuevamente.'}</p>`);
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
            rows = (result.rows || []).filter(r => paying || r.request).map(r => ({...r, selected: false,
                disabled: r.payment_status === 'Paid' || (paying && (['Rejected', 'Cancelled'].includes(r.approval_status) || r.source_work_call !== frm.doc.name))}));
            render();
        }
        dialog.show(); load();
    }

    function confirmPayment(preview, args, done) {
        // Keep this exact key and payload on transport failure so retry is safe.
        const key = crypto.randomUUID();
        const confirm = new frappe.ui.Dialog({title: 'Confirmar pagos realizados', fields: [{fieldname: 'preview', fieldtype: 'HTML'}],
            primary_action_label: 'Confirmar pagos realizados', primary_action: async () => {
                confirm.disable_primary_action();
                try {
                    const result = await call(api + 'confirm_payout', {...args, token: preview.token, idempotency_key: key});
                    confirm.hide(); await done(result);
                } finally { confirm.enable_primary_action(); }
            }});
        confirm.fields_dict.preview.$wrapper.html(`<p>Se aprobarán estos montos y se registrará el dinero como entregado. Esta acción no realiza transferencias bancarias.</p>
            <ul>${preview.rows.map(r => `<li>${esc(r.employee_name)}: ${amount(r.amount, preview.currency)}</li>`).join('')}</ul>
            <p><strong>${preview.rows.length} empleados · ${amount(preview.total, preview.currency)}</strong></p>
            <p>${esc(preview.payment.payment_date)} · ${esc(preview.payment.mode_of_payment)}</p>`);
        confirm.show();
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
                <p>Fecha de trabajo: ${esc(b.work_date)} · Registrado por: ${esc(b.paid_by)} · ${esc(b.paid_on)}</p>
                <p>Referencia: ${esc(b.reference)} · Contabilidad: ${esc(label(b.accounting_status))}</p>
                <p>${esc(b.accounting_error)}</p><p>Comprobante: ${esc(b.evidence || "Sin adjunto")}</p><ul>${b.rows.map(r => `<li>${esc(r.employee_name)}: ${esc(r.amount)}</li>`).join('')}</ul>
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
    frappe.ui.form.on('Overtime Work Call', {refresh: frm => refresh(frm).catch(() => {})});
})();
