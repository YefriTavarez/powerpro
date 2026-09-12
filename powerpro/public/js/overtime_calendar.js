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
			<p>${escape(__(result.evidence_source))}</p>
			<p>${escape(__("Comparación de referencia anterior. No aplica las políticas versionadas del motor por marcaciones ni determina el pago vigente."))}</p>`;
		html += table(["Concepto", "Referencia anterior", "Por fecha (referencia)", "Diferencia"],
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
		if (result.weekly_evidence) {
			const weekly = result.weekly_evidence;
			html += `<h5>${escape(__("Evidencia semanal provisional"))}</h5>`;
			for (const week of weekly.weeks || []) {
				html += `<p>${escape(__("Semana desde"))} ${escape(week.week_start)}</p>`;
				if (week.truncated) {
					html += `<p>${escape(__("Demasiadas marcaciones: no se calcula un total con evidencia truncada."))}</p>`;
					continue;
				}
				html += table(["Horas de pares IN/OUT", "Antes de la autorización", "Umbral configurado", "Distancia provisional al umbral"], [[
					hours(week.paired_hours), hours(week.hours_before_cutoff), hours(week.configured_threshold), hours(week.provisional_hours_to_threshold)]]);
				html += `<p>${escape(__("Horas extras regulares previas usadas por la referencia anterior"))}: ${hours(week.legacy_regular_overtime_before)}</p>`;
				if (week.shift_comparison) {
					const shifted = week.shift_comparison;
					const hasShiftIntervals = shifted.sessions.some((row) => row.hours > 0);
					const hasCorrectedIntervals = hasShiftIntervals || shifted.applied_corrections.length > 0;
					const eligibleHours = (value, available) => available ? hours(value) : __("Sin evidencia elegible");
					html += `<h5>${escape(__("Comparación con turno y Gestión Humana"))}</h5>`;
					html += table(["Lectura", "Total semanal provisional", "Antes de la autorización"], [
						[__("Pares IN/OUT explícitos"), hours(week.paired_hours), hours(week.hours_before_cutoff)],
						[__("Según reglas del turno"), eligibleHours(shifted.configured.paired_hours, hasShiftIntervals), eligibleHours(shifted.configured.hours_before_cutoff, hasShiftIntervals)],
						[__("Turno con correcciones aplicadas"), eligibleHours(shifted.with_corrections.paired_hours, hasCorrectedIntervals), eligibleHours(shifted.with_corrections.hours_before_cutoff, hasCorrectedIntervals)]]);
					html += `<details><summary>${escape(__("Ver turnos, correcciones y advertencias"))}</summary>`;
					html += table(["Turno guardado", "Inicio del turno", "Horas", "Interpretación", "Cálculo"],
						shifted.sessions.map((row) => [row.shift, row.shift_start, hours(row.hours), __(row.direction_rule), __(row.hours_rule)]));
					if (shifted.applied_corrections.length) html += table(["Corrección aplicada", "Tipo", "Desde", "Hasta"],
						shifted.applied_corrections.map((row) => [row.name, __(row.kind), row.start, row.end]));
					const issueLabels = {skip_auto_attendance:"Excluida de asistencia automática", offshift:"Fuera de turno",
						missing_shift_window:"Sin horario de turno guardado", invalid_shift_window:"Horario de turno inválido",
						outside_captured_window:"Fuera de la ventana guardada", unavailable_shift_policy:"Reglas del turno no disponibles",
						unsupported_shift_policy:"Reglas del turno no reconocidas", duplicate_timestamp:"Marcaciones simultáneas",
						insufficient_shift_punches:"Faltan marcaciones del turno", odd_alternating_count:"Cantidad impar de marcaciones",
						direction_reinterpreted:"Dirección interpretada por alternancia", consecutive_in:"Entradas consecutivas",
						out_without_in:"Salida sin entrada", unknown_direction:"Dirección desconocida", in_without_out:"Entrada sin salida",
						first_last_includes_breaks:"Primera/última incluye el tiempo intermedio", invalid_duration:"Duración inválida",
						invalid_correction:"Corrección inválida", overlapping_corrections:"Correcciones superpuestas: requieren revisión"};
					if (shifted.issues.length) html += table(["Advertencia", "Referencia"], shifted.issues.map((row) => [
						__(issueLabels[row.code] || row.code), row.source || (row.checkins || []).join(", ")]));
					html += list(shifted.notes || []);
					html += `</details>`;
				}
				const statuses = {review: "Revisar marcaciones", paired_evidence: "Con pares; cobertura no certificada", no_paired_evidence: "Sin pares; no confirma ausencia"};
				html += table(["Fecha", "Horas reconstruidas", "Marcaciones", "Estado"],
					week.days.map((day) => [day.date, hours(day.paired_hours), day.punch_count, __(statuses[day.status] || day.status)]));
				if (week.offshift_punches) html += `<p>${escape(__("Marcaciones fuera de turno que requieren revisión"))}: ${Number(week.offshift_punches)}</p>`;
				const issues = {duplicate_timestamp: "Marcaciones con la misma hora", ambiguous_pair: "Par ambiguo excluido",
					unknown_direction: "Dirección desconocida", consecutive_in: "Entradas consecutivas", out_without_in: "Salida sin entrada",
					invalid_duration: "Duración inválida o superior a 24 horas", in_without_out: "Entrada sin salida"};
				if (week.issues.length) html += table(["Incidencia", "Marcaciones de origen"],
					week.issues.map((item) => [__(issues[item.code] || item.code), item.checkins.join(", ")]));
			}
			html += `<div class="alert alert-info">${list(weekly.notes || [])}</div>`;
		}
		if (result.overnight && result.overnight.applicable) {
			const night = result.overnight;
			html += `<h5>${escape(__("Madrugada y autorización"))}</h5>`;
			if (night.available) {
				const labels = {"Needs Review":"Requiere revisión", "Previous authorized session":"Posible continuación de la jornada autorizada"};
				if (night.interpretations.length) html += table(["Marcación", "Hora", "Tipo guardado", "Interpretación propuesta"],
					night.interpretations.map((r) => [r.checkin, r.time, r.stored_log_type, __(labels[r.interpretation] || r.interpretation)]));
				if (night.intervals.length) html += table(["Inicio propuesto de trabajo", "Fin propuesto de trabajo"],night.intervals.map((r) => [r.start,r.end]));
				const reasons = {incomplete_shift_context:"No se pudo confirmar el contexto de turnos",
					authorization_not_ended:"La autorización todavía no ha terminado",overlapping_authorizations:"Hay autorizaciones superpuestas",
					missing_shift_policy:"Faltan las reglas del turno",sync_not_confirmed:"La sincronización no cubre el fin autorizado",
					excluded_checkins:"Hay marcaciones excluidas de Auto Attendance",missing_captured_anchor:"Falta el turno de origen en las marcaciones elegibles",
					extended_session_over_24h:"La jornada extendida supera el límite de revisión de 24 horas",
					next_shift_overlap:"Una marcación también cabe en el turno siguiente",adjacent_shift_overlap:"Una marcación también cabe en el turno anterior",punch_sequence_requires_review:"La secuencia de marcaciones requiere revisión",
					missing_worked_interval:"Faltan intervalos de trabajo calculables"};
				if (night.coverage_blockers.length) html += `<div class="alert alert-warning">${list(night.coverage_blockers.map((r) => reasons[r] || r))}</div>`;
			}
			html += list(night.notes || []);
		}
		if (result.pricing) {
			const price = result.pricing;
			const money = (value) => `${price.currency} ${Number(value || 0).toFixed(2)}`;
			html += `<h5>${escape(__("Importes ilustrativos de referencia"))}</h5>`;
			html += table(["Referencia anterior", "Por fecha (referencia)", "Diferencia"], [[
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
