/* Read-only comparison; intentionally exposes no save or settlement action. */
frappe.provide("powerpro.overtime_calendar");

(() => {
	const api = powerpro.overtime_calendar;
	const escape = (value) => frappe.utils.escape_html(String(value ?? ""));
	const hours = (value) => Number(value || 0).toFixed(4);
	const fields = [
		["verified_hours", "Horas calculadas"],
		["regular_35_hours", "Horas extras +35%"],
		["regular_100_hours", "Horas extras +100%"],
		["holiday_100_hours", "Horas en feriado +100%"],
		["weekly_rest_hours", "Horas en descanso semanal"],
		["night_hours", "Horas en horario nocturno"],
	];
	const labels = {"Regular Workday": "Día laborable regular", "Legal Holiday": "Feriado",
		"Weekly Rest": "Descanso semanal", "Legal Holiday on Weekly Rest": "Feriado en descanso semanal"};
	const table = (headers, rows) => `<div class="table-responsive"><table class="table table-bordered">
		<thead><tr>${headers.map((value) => `<th>${escape(__(value))}</th>`).join("")}</tr></thead>
		<tbody>${rows.map((row) => `<tr>${row.map((value) => `<td>${escape(value)}</td>`).join("")}</tr>`).join("")}</tbody>
		</table></div>`;
	const list = (rows) => `<ul>${rows.map((value) => `<li>${escape(__(value))}</li>`).join("")}</ul>`;
	api.render = (result) => {
		let html = `<p><strong>${escape(__("Vista previa de solo lectura"))}</strong> · ${escape(result.name)}</p>
			<p>${escape(__(result.evidence_source))}</p>`;
		html += table(["Concepto", "Vigente recalculado", "Por fecha", "Diferencia"],
			fields.map(([field, label]) => [__(label), hours(result.baseline[field]),
				hours(result.proposed[field]), hours(result.difference[field])]));
		const segments = result.proposed.segments || [];
		if (segments.length) {
			html += `<h5>${escape(__("Detalle por fecha"))}</h5>`;
			html += table(["Fecha", "Inicio", "Fin", "Clasificación", "Horas", "Nocturnas"],
				segments.map((row) => [row.date, row.start.replace("T", " "), row.end.replace("T", " "),
					__(labels[row.classification] || row.classification), hours(row.verified_hours), hours(row.night_hours)]));
		} else {
			html += `<p>${escape(__("No hay intervalos calculables con la evidencia disponible."))}</p>`;
		}
		if (result.proposed.excluded_by_maximum_hours > 0) {
			html += `<p>${escape(__("Horas que exceden el máximo autorizado"))}: ${hours(result.proposed.excluded_by_maximum_hours)}</p>`;
		}
		if (result.pricing) {
			const price = result.pricing;
			const money = (value) => `${price.currency} ${Number(value || 0).toFixed(2)}`;
			html += `<h5>${escape(__("Importes ilustrativos con las tasas actuales"))}</h5>`;
			html += table(["Vigente recalculado", "Por fecha", "Diferencia"], [[
				money(price.baseline.total_amount), money(price.proposed.total_amount), money(price.difference)]]);
			html += `<p>${escape(__(price.rate_source))}: ${escape(money(price.hourly_rate))}</p>`;
		} else if (result.pricing_note) {
			html += `<p>${escape(__(result.pricing_note))}</p>`;
		}
		if (result.warnings.length) html += `<div class="alert alert-warning">${list(result.warnings)}</div>`;
		html += `<div class="text-muted">${list(result.assumptions)}</div>`;
		return html;
	};
	api.show = (doctype, name) => frappe.call({
		method: "powerpro.controllers.overtime_calendar.get_calendar_comparison",
		args: {doctype, name}, freeze: true,
		freeze_message: __("Comparando los intervalos por fecha..."),
	}).then(({message}) => frappe.msgprint({title: __("Comparación de horas por fecha"),
		message: api.render(message), wide: true}));
	api.add_button = (frm) => {
		if (frm.is_new() || frm.doc.docstatus === 2) return;
		frm.add_custom_button(__("Comparar cálculo por fecha"), () => {
			if (frm.is_dirty()) {
				frappe.msgprint(__("Guarde los cambios antes de comparar. La vista previa usa el documento guardado."));
				return;
			}
			if (frm.doc.doctype !== "Overtime Work Call") return api.show(frm.doc.doctype, frm.doc.name);
			return frappe.call({method: "powerpro.controllers.overtime_calendar.get_work_call_comparison_options",
				args: {work_call: frm.doc.name}}).then(({message}) => {
				if (!message.rows.length) return frappe.msgprint(__("No hay autorizaciones disponibles para comparar."));
				const dialog = new frappe.ui.Dialog({title: __("Seleccionar autorización"), fields: [{
					fieldname: "authorization", fieldtype: "Select", label: __("Autorización"), reqd: 1,
					options: message.rows.map((row) => ({value: row.name,
						label: `${row.employee_name} · ${row.work_date} · ${row.name}`})),
					description: message.has_more ? __("Se muestran las primeras 100. Puede abrir otra autorización directamente.") : "",
				}], primary_action_label: __("Comparar"), primary_action(values) {
					dialog.hide();
					return api.show("Overtime Authorization", values.authorization);
				}});
				dialog.show();
			});
		}, __("Overtime"));
	};
})();
