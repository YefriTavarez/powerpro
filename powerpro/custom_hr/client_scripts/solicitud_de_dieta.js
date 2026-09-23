// Presentation and controlled edits; approval/payment remain in the Work Call service.
(() => {
	const escape = (value) => frappe.utils.escape_html(String(value ?? ""));
	const approval = {
		Pending: ["Pendiente", "orange"], Approved: ["Aprobado", "green"],
		Rejected: ["Rechazado", "red"], Cancelled: ["Cancelado", "gray"],
	};
	const payment = { Unpaid: ["Impagada", "orange"], Paid: ["Pagada", "green"] };
	const actions = {
		request: "Solicitud creada", approve: "Solicitud aprobada", reject: "Solicitud rechazada",
		amount: "Monto actualizado", edit: "Solicitud editada", reconsider: "Solicitud reconsiderada",
		approve_and_pay: "Aprobación y pago", confirm_payment: "Pago confirmado",
		authorization_cancelled: "Autorización cancelada", attendance_review: "Revisión de asistencia",
	};
	const labels = {
		previous_amount: "Monto anterior", amount: "Monto", default_amount: "Importe por defecto", previous_notes: "Notas anteriores",
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

// Saved requests are edited through a narrow API, never through savedocs.
(() => {
	const api = "powerpro.dietas.request_edit.";
	const escape = (value) => frappe.utils.escape_html(String(value ?? ""));
	const editable_fields = ["employee", "company", "work_date", "overtime_work_call", "authorization", "amount", "currency", "notes"];

	async function edit_request(frm) {
		const name = frm.doc.name;
		const { message: context } = await frappe.call({ method: api + "get_context", args: { request: name } });
		if (frm.doc.name !== name) return;
		if (!context.can_edit) {
			frappe.msgprint(__("La solicitud ya no se puede editar. Recargue el documento."));
			return;
		}
		let saving = false;
		const dialog = new frappe.ui.Dialog({
			title: __("Editar solicitud de dieta"),
			fields: [
				{ fieldname: "currency", fieldtype: "Data", hidden: 1, default: context.currency },
				{ fieldname: "amount", fieldtype: "Currency", label: __("Monto"), options: "currency", reqd: 1, default: context.amount },
				{ fieldname: "notes", fieldtype: "Small Text", label: __("Notas"), default: context.notes,
					description: __("Indique el motivo si el monto difiere del importe por defecto.") },
			],
			primary_action_label: __("Guardar cambios"),
			async primary_action(values) {
				if (saving) return;
				saving = true;
				dialog.get_primary_btn().prop("disabled", true);
				try {
					await frappe.call({ method: api + "update_request", args: {
						request: name, modified: context.modified, amount: values.amount, notes: values.notes || "",
					} });
					dialog.hide();
					if (frm.doc.name === name) await frm.reload_doc();
				} finally {
					saving = false;
					dialog.get_primary_btn().prop("disabled", false);
				}
			},
		});
		dialog.show();
	}

	frappe.ui.form.on("Solicitud de Dieta", {
		async refresh(frm) {
			const is_new = frm.is_new();
			editable_fields.forEach((field) => frm.set_df_property(field, "read_only", is_new ? 0 : 1));
			if (is_new) { frm.enable_save(); return; }
			frm.disable_save();
			frm.remove_custom_button(__("Editar solicitud"));
			frm.remove_custom_button(__("Abrir convocatoria"));
			const name = frm.doc.name;
			const refresh_id = (frm.__dieta_refresh_id || 0) + 1;
			frm.__dieta_refresh_id = refresh_id;
			const { message: context } = await frappe.call({ method: api + "get_context", args: { request: name } });
			if (frm.doc.name !== name || frm.__dieta_refresh_id !== refresh_id) return;
			if (context.can_edit) frm.add_custom_button(__("Editar solicitud"), () => edit_request(frm));
			let message = context.can_edit ? __("Puede corregir monto y notas con Editar solicitud.") : "";
			if (context.payment_status === "Unpaid") {
				if (context.expense_approver) message += " " + __("Aprobador asignado:") + " " + escape(context.expense_approver) + ".";
				if (context.work_call) {
					message += " " + __("La aprobación y el registro del pago se gestionan desde la convocatoria.");
					frm.add_custom_button(__("Abrir convocatoria"), () => frappe.set_route("Form", "Overtime Work Call", context.work_call));
				} else {
					message += " " + __("La aprobación y el pago de solicitudes sin convocatoria todavía no están disponibles. Guardar no aprueba ni registra un pago.");
				}
			}
			frm.set_intro(message.trim(), context.work_call || context.payment_status === "Paid" ? "blue" : "orange");
		},
	});
})();
