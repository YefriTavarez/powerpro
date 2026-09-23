(() => {
	const escape = (value) => frappe.utils.escape_html(String(value ?? ""));
	const money = (value, doc) => escape(format_currency(value || 0, doc.currency));
	const date = (value) => value ? escape(frappe.datetime.str_to_user(value)) : "-";
	const states = {
		Confirmed: ["Confirmado", "green"],
		Reversed: ["Corregido", "gray"],
		Disabled: ["Deshabilitado", "gray"],
		Pending: ["Pendiente", "orange"],
		Draft: ["Borrador", "blue"],
		Posted: ["Contabilizado", "green"],
		Cancelled: ["Cancelado", "gray"],
		Error: ["Revisar", "red"],
	};
	const actions = {
		confirm_payment: "Pago confirmado",
		journal_draft: "Borrador contable generado",
		journal_status: "Estado contable actualizado",
		reverse_erroneous_payment: "Registro de pago corregido",
	};
	const detailLabels = {
		total: "Total",
		journal_entry: "Asiento contable",
		accounting_status: "Estado contable",
		reason: "Motivo",
	};
	const label = (value) => states[value]?.[0] || value || "Sin estado";
	const badge = (value) => {
		const [text, color] = states[value] || [value || "Sin estado", "gray"];
		return `<span class="indicator-pill ${color}">${escape(text)}</span>`;
	};

	function render_summary(frm) {
		if (!frm.fields_dict.summary) return;
		const doc = frm.doc;
		const employeeCount = (doc.rows || []).length;
		frm.fields_dict.summary.$wrapper.html(`
			<style>
				.dieta-payment-summary { display: grid; grid-template-columns: minmax(220px, 1.5fr) repeat(3, minmax(130px, 1fr));
					gap: 16px; padding: 20px 22px; border: 1px solid var(--border-color); border-radius: 8px;
					background: var(--subtle-fg); margin-bottom: 8px; }
				.dieta-payment-card { min-width: 0; }
				.dieta-payment-caption { color: var(--text-muted); font-size: var(--text-sm); margin-bottom: 7px; }
				.dieta-payment-total { color: var(--text-color); font-size: 28px; font-weight: 650; line-height: 1.15; }
				.dieta-payment-meta { color: var(--text-muted); font-size: var(--text-sm); margin-top: 8px; overflow-wrap: anywhere; }
				.dieta-payment-status { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
				.dieta-payment-warning { margin-top: 12px; padding: 12px 14px; border-radius: 8px; background: var(--alert-bg-danger);
					color: var(--text-color); overflow-wrap: anywhere; }
				@media (max-width: 900px) { .dieta-payment-summary { grid-template-columns: 1fr 1fr; } }
				@media (max-width: 560px) { .dieta-payment-summary { grid-template-columns: 1fr; } }
			</style>
			<section class="dieta-payment-summary">
				<div class="dieta-payment-card">
					<div class="dieta-payment-caption">Total pagado</div>
					<div class="dieta-payment-total">${money(doc.total, doc)}</div>
					<div class="dieta-payment-meta">${employeeCount} empleado${employeeCount === 1 ? "" : "s"} · ${escape(doc.mode_of_payment || "Sin método")}</div>
				</div>
				<div class="dieta-payment-card">
					<div class="dieta-payment-caption">Pago</div>
					<div class="dieta-payment-status">${badge(doc.status)}</div>
					<div class="dieta-payment-meta">${date(doc.payment_date)}</div>
				</div>
				<div class="dieta-payment-card">
					<div class="dieta-payment-caption">Trabajo</div>
					<strong>${date(doc.work_date)}</strong>
					<div class="dieta-payment-meta">${escape(doc.overtime_work_call || "")}</div>
				</div>
				<div class="dieta-payment-card">
					<div class="dieta-payment-caption">Contabilidad</div>
					<div class="dieta-payment-status">${badge(doc.accounting_status)}</div>
					<div class="dieta-payment-meta">${doc.journal_entry ? escape(doc.journal_entry) : "Sin asiento"}</div>
				</div>
			</section>
			${doc.accounting_error ? `<div class="dieta-payment-warning"><strong>Contabilidad por revisar:</strong> ${escape(doc.accounting_error)}</div>` : ""}
		`);
	}

	function render_history(frm) {
		if (!frm.fields_dict.audit_timeline) return;
		let events;
		try {
			events = JSON.parse(frm.doc.audit_log || "[]");
			if (!Array.isArray(events)) throw new Error("Invalid audit history");
		} catch {
			frm.fields_dict.audit_timeline.$wrapper.html('<p class="text-muted">No se pudo mostrar el historial. Consulte el registro técnico.</p>');
			return;
		}
		const html = events.slice().reverse().map((event) => {
			const details = Object.entries(event).filter(([key]) => !["action", "user", "at"].includes(key))
				.map(([key, value]) => {
					let display = value;
					if (key === "total" && typeof value === "number") display = format_currency(value, frm.doc.currency);
					if (key === "accounting_status") display = label(value);
					if (value && typeof value === "object") display = JSON.stringify(value);
					return `<div><span>${escape(detailLabels[key] || key)}:</span> ${escape(display)}</div>`;
				}).join("");
			return `<article class="dieta-payment-event">
				<div class="dieta-payment-event-heading">
					<strong>${escape(actions[event.action] || event.action || "Actividad")}</strong>
					<span>${date(event.at)}</span>
				</div>
				<div class="dieta-payment-event-meta">${escape(event.user || "")}</div>
				<div class="dieta-payment-event-details">${details}</div>
			</article>`;
		}).join("");
		frm.fields_dict.audit_timeline.$wrapper.html(`
			<style>
				.dieta-payment-event { border-left: 2px solid var(--border-color); margin-left: 6px; padding: 0 0 20px 18px; }
				.dieta-payment-event:last-child { padding-bottom: 4px; }
				.dieta-payment-event-heading { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px; }
				.dieta-payment-event-heading span, .dieta-payment-event-meta, .dieta-payment-event-details span {
					color: var(--text-muted); font-size: var(--text-sm); }
				.dieta-payment-event-meta { margin: 5px 0 10px; }
				.dieta-payment-event-details { display: flex; flex-wrap: wrap; gap: 8px 22px; font-size: var(--text-sm); overflow-wrap: anywhere; }
			</style>
			${html || '<p class="text-muted">Todavía no hay actividad registrada.</p>'}
		`);
	}

	frappe.ui.form.on("Lote de Pago de Dietas", {
		refresh(frm) { render_summary(frm); render_history(frm); },
		total: render_summary,
		currency: render_summary,
		mode_of_payment: render_summary,
		payment_date: render_summary,
		work_date: render_summary,
		status: render_summary,
		accounting_status: render_summary,
		accounting_error: render_summary,
		journal_entry: render_summary,
		audit_log: render_history,
	});
})();
