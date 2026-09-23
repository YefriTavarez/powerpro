// Presentation only: business actions remain in the Dietas service / Work Call.
(() => {
	const escape = (value) => frappe.utils.escape_html(String(value ?? ""));
	const approval = {
		Pending: ["Pendiente", "orange"], Approved: ["Aprobado", "green"],
		Rejected: ["Rechazado", "red"], Cancelled: ["Cancelado", "gray"],
	};
	const payment = { Unpaid: ["Impagada", "orange"], Paid: ["Pagada", "green"] };
	const actions = {
		request: "Solicitud creada", approve: "Solicitud aprobada", reject: "Solicitud rechazada",
		amount: "Monto actualizado", reconsider: "Solicitud reconsiderada",
		approve_and_pay: "Aprobación y pago", confirm_payment: "Pago confirmado",
		authorization_cancelled: "Autorización cancelada", attendance_review: "Revisión de asistencia",
	};
	const labels = {
		previous_amount: "Monto anterior", amount: "Monto", default_amount: "Importe por defecto",
		previous_status: "Estado anterior", origin: "Origen", authorization: "Autorización",
		total: "Total", payout_batch: "Lote de pago", payment_status: "Estado del pago",
	};
	const money = (value, doc) => escape(format_currency(value, doc.currency, 2));
	const date = (value) => value ? escape(frappe.datetime.str_to_user(value)) : "—";
	const badge = (value, states) => {
		const [label, color] = states[value] || [value || "Sin estado", "gray"];
		return `<span class="indicator-pill ${color}">${escape(label)}</span>`;
	};

	function render_summary(frm) {
		const doc = frm.doc;
		if (!frm.fields_dict.summary) return;
		frm.fields_dict.summary.$wrapper.html(`
			<style>
				.dieta-overview { display: flex; flex-wrap: wrap; gap: 24px; padding: 22px 24px;
					border: 1px solid var(--border-color); border-radius: 12px; background: var(--subtle-fg); margin-bottom: 8px; }
				.dieta-overview-item { flex: 1 1 150px; }
				.dieta-caption { color: var(--text-muted); font-size: var(--text-sm); margin-bottom: 8px; }
				.dieta-amount { font-size: 26px; font-weight: 650; line-height: 1.2; color: var(--text-color); }
				.dieta-date { color: var(--text-muted); font-size: var(--text-sm); margin-top: 8px; }
				.dieta-review { margin-top: 12px; }
				.dieta-event { border-left: 2px solid var(--border-color); padding: 0 0 22px 20px; margin-left: 6px; }
				.dieta-event:last-child { padding-bottom: 4px; }
				.dieta-event-heading { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px; }
				.dieta-event-meta { color: var(--text-muted); font-size: var(--text-sm); margin: 5px 0 10px; }
				.dieta-event-reason { background: var(--subtle-fg); padding: 12px 14px; border-radius: 8px;
					margin-bottom: 10px; white-space: pre-wrap; overflow-wrap: anywhere; }
				.dieta-event-details { display: flex; flex-wrap: wrap; gap: 10px 24px; font-size: var(--text-sm); overflow-wrap: anywhere; }
				.dieta-event-details span { color: var(--text-muted); }
			</style>
			<div class="dieta-overview">
				<div class="dieta-overview-item"><div class="dieta-caption">Monto de la dieta</div>
					<div class="dieta-amount">${money(doc.amount, doc)}</div>
					<div class="dieta-date">Fecha de trabajo · ${date(doc.work_date)}</div></div>
				<div class="dieta-overview-item"><div class="dieta-caption">Aprobación</div>${badge(doc.approval_status, approval)}</div>
				<div class="dieta-overview-item"><div class="dieta-caption">Pago</div>${badge(doc.payment_status, payment)}</div>
			</div>
			${doc.review_required ? '<div class="dieta-review indicator-pill orange">Revisión requerida · Consulte las observaciones</div>' : ""}
		`);
	}

	function render_history(frm) {
		if (!frm.fields_dict.audit_timeline) return;
		let events;
		try {
			events = JSON.parse(frm.doc.audit_log || "[]");
			if (!Array.isArray(events) || events.some((event) => !event || typeof event !== "object" || Array.isArray(event))) {
				throw new Error("Invalid audit history");
			}
		} catch {
			frm.fields_dict.audit_timeline.$wrapper.html('<p class="text-muted">No se pudo mostrar el historial. Consulte el registro técnico.</p>');
			return;
		}
		const html = events.slice().reverse().map((event) => {
			const details = Object.entries(event).filter(([key]) => !["action", "reason", "user", "at"].includes(key))
				.map(([key, value]) => {
					let display;
					if (["amount", "previous_amount", "default_amount", "total"].includes(key) && typeof value === "number") {
						display = money(value, frm.doc);
					} else {
						const translated = approval[value]?.[0] || payment[value]?.[0] || ({ Employee: "Empleado", Manager: "Administrador" })[value];
						display = escape(translated || (typeof value === "object" ? JSON.stringify(value) : value));
					}
					return `<div><span>${escape(labels[key] || key)}:</span> ${display}</div>`;
				}).join("");
			return `<article class="dieta-event">
				<div class="dieta-event-heading"><strong>${escape(actions[event.action] || event.action || "Actividad")}</strong>
					<span class="text-muted">${date(event.at)}</span></div>
				<div class="dieta-event-meta">${escape(event.user || "")}</div>
				${event.reason ? `<div class="dieta-event-reason">${escape(event.reason)}</div>` : ""}
				<div class="dieta-event-details">${details}</div>
			</article>`;
		}).join("");
		frm.fields_dict.audit_timeline.$wrapper.html(html || '<p class="text-muted">Todavía no hay actividad registrada.</p>');
	}

	frappe.ui.form.on("Solicitud de Dieta", {
		refresh(frm) { render_summary(frm); render_history(frm); },
		amount: render_summary,
		currency: render_summary,
		work_date: render_summary,
		approval_status: render_summary,
		payment_status: render_summary,
		review_required: render_summary,
		audit_log: render_history,
	});
})();
