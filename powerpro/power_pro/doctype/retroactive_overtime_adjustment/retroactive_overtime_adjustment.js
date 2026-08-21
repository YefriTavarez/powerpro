// Copyright (c) 2026, PowerPro contributors
// For license information, please see license.txt

frappe.ui.form.on("Retroactive Overtime Adjustment", {
	refresh(frm) {
		configure_reconciliation_display(frm);

		if (frm.doc.docstatus === 0) {
			frm.dashboard.set_headline_alert(
				__("Historical overtime is an audited exception and requires existing Employee Checkin evidence."),
				"orange"
			);
			load_draft_reconciliation_preview(frm);
		}

		if (!frm.is_new() && frm.doc.docstatus < 2) {
			const label = frm.doc.docstatus === 1
				? __("Reconciliation Snapshot")
				: __("Refresh Reconciliation Preview");
			frm.add_custom_button(label, () => {
				if (frm.doc.docstatus === 0) {
					load_draft_reconciliation_preview(frm, { freeze: true, show_dialog: true });
					return;
				}

				get_retroactive_reconciliation(frm, { freeze: true })
					.then((result) => show_retroactive_reconciliation(result));
			}, __("Overtime"));
		}
	},

	employee: mark_reconciliation_preview_stale,
	work_date: mark_reconciliation_preview_stale,
	authorization_start: mark_reconciliation_preview_stale,
	authorization_end: mark_reconciliation_preview_stale,
	maximum_hours: mark_reconciliation_preview_stale,
	planned_settlement(frm) {
		if (frm.doc.docstatus !== 0) {
			return;
		}
		if (frm.__retroactive_overtime_preview) {
			render_draft_reconciliation_preview(
				frm,
				frm.__retroactive_overtime_preview
			);
		}
	},
});

const SNAPSHOT_FIELDS = [
	"verified_hours",
	"regular_35_hours",
	"regular_100_hours",
	"holiday_100_hours",
	"weekly_rest_hours",
	"night_hours",
	"reconciliation_warnings",
	"reconciliation_intervals",
	"source_checkins",
	"reconciled_by",
	"reconciled_on",
];

function configure_reconciliation_display(frm) {
	const is_draft = frm.doc.docstatus === 0;
	frm.set_df_property(
		"reconciliation_section",
		"label",
		is_draft ? __("Reconciliation Preview") : __("Reconciliation Snapshot")
	);
	frm.toggle_display("draft_reconciliation_preview", is_draft);
	SNAPSHOT_FIELDS.forEach((fieldname) => frm.toggle_display(fieldname, !is_draft));
}

function mark_reconciliation_preview_stale(frm) {
	if (frm.doc.docstatus !== 0 || frm.is_new()) {
		return;
	}
	frm.__retroactive_overtime_preview = null;
	render_preview_message(
		frm,
		__("Save the draft to recalculate the reconciliation preview."),
		"orange"
	);
}

function get_retroactive_reconciliation(frm, { freeze = false } = {}) {
	return frappe.call({
		method: "powerpro.controllers.overtime.get_retroactive_adjustment_preview",
		args: { adjustment: frm.doc.name },
		freeze,
		freeze_message: __("Comparing historical approval, shift, holiday, and punches..."),
	}).then(({ message }) => message);
}

function load_draft_reconciliation_preview(
	frm,
	{ freeze = false, show_dialog = false } = {}
) {
	if (frm.doc.docstatus !== 0) {
		return Promise.resolve(null);
	}
	if (frm.is_new()) {
		render_preview_message(
			frm,
			__("Save the draft to calculate the reconciliation preview."),
			"blue"
		);
		return Promise.resolve(null);
	}
	if (frm.is_dirty()) {
		render_preview_message(
			frm,
			__("Save the draft to recalculate the reconciliation preview."),
			"orange"
		);
		return Promise.resolve(null);
	}

	render_preview_message(frm, __("Calculating reconciliation preview..."), "blue");
	return get_retroactive_reconciliation(frm, { freeze })
		.then((result) => {
			frm.__retroactive_overtime_preview = result;
			render_draft_reconciliation_preview(frm, result);
			if (show_dialog) {
				show_retroactive_reconciliation(result);
			}
			return result;
		})
		.catch(() => {
			render_preview_message(
				frm,
				__("The reconciliation preview could not be calculated. Review the form and try again."),
				"red"
			);
			return null;
		});
}

function render_preview_message(frm, message, indicator) {
	const wrapper = frm.fields_dict.draft_reconciliation_preview?.$wrapper;
	if (!wrapper) {
		return;
	}
	const escaped_message = frappe.utils.escape_html(String(message));
	const alert_class = indicator === "red"
		? "danger"
		: indicator === "orange" ? "warning" : "info";
	wrapper.html(
		`<div class="alert alert-${alert_class}">${escaped_message}</div>`
	);
}

function render_draft_reconciliation_preview(frm, result) {
	const wrapper = frm.fields_dict.draft_reconciliation_preview?.$wrapper;
	if (!wrapper) {
		return;
	}

	const rows = get_reconciliation_rows(result);
	const body = rows
		.map(([label, value]) => (
			`<tr><td>${escape_value(label)}</td>`
			+ `<td class="text-right"><strong>${escape_value(value)}</strong></td></tr>`
		))
		.join("");
	const warnings = render_warnings(result.warnings);
	const intervals = (result.intervals || [])
		.map((interval) => (
			`<li>${escape_value(interval.start)} &rarr; ${escape_value(interval.end)}</li>`
		))
		.join("");
	const settlement_note = frm.doc.planned_settlement === "Cash"
		? __("Cash is the planned settlement. This preview does not create a payment or Additional Salary.")
		: __("Compensatory Rest is the planned settlement. This preview does not create leave or a Leave Allocation.");

	wrapper.html(`
		<div class="alert alert-info">
			<strong>${escape_value(__("Draft calculation — not yet approved"))}</strong><br>
			${escape_value(__("Submission recalculates these values and stores the authoritative snapshot."))}
		</div>
		<table class="table table-bordered"><tbody>${body}</tbody></table>
		${intervals ? `<p><strong>${escape_value(__("Verified intervals"))}</strong></p><ul>${intervals}</ul>` : ""}
		${warnings}
		<p class="text-muted">${escape_value(settlement_note)}</p>
	`);
}

function format_hours(value) {
	return `${format_number(value || 0, null, 4)} ${__("hours")}`;
}

function get_reconciliation_rows(result) {
	const rates = result.rates || {};
	const extraordinary_rate = rates.extraordinary_overtime_percent ?? 100;
	return [
		[__("Classification"), result.classification],
		[__("Verified hours"), format_hours(result.verified_hours)],
		[
			__("Regular overtime +{0}%", [rates.regular_overtime_percent ?? 35]),
			format_hours(result.regular_35_hours),
		],
		[
			__("Regular overtime +{0}%", [extraordinary_rate]),
			format_hours(result.regular_100_hours),
		],
		[
			__("Legal holiday +{0}%", [extraordinary_rate]),
			format_hours(result.holiday_100_hours),
		],
		[__("Weekly rest"), format_hours(result.weekly_rest_hours)],
		[
			__("Night hours +{0}%", [rates.night_hours_percent ?? 15]),
			format_hours(result.night_hours),
		],
	];
}

function escape_value(value) {
	return frappe.utils.escape_html(String(value ?? ""));
}

function render_warnings(warnings) {
	const items = (warnings || [])
		.filter(Boolean)
		.map((warning) => `<li>${escape_value(warning)}</li>`)
		.join("");
	if (!items) {
		return `<p class="text-success"><strong>${escape_value(__("No reconciliation warnings."))}</strong></p>`;
	}
	return `<div class="alert alert-warning"><strong>${escape_value(__("Warnings"))}</strong><ul>${items}</ul></div>`;
}

function show_retroactive_reconciliation(result) {
	const rows = get_reconciliation_rows(result);
	const body = rows
		.map(([label, value]) => `<tr><td>${frappe.utils.escape_html(String(label))}</td><td class="text-right">${frappe.utils.escape_html(String(value))}</td></tr>`)
		.join("");
	const warnings = render_warnings(result.warnings);
	const snapshot = result.snapshot
		? `<p class="text-muted">${__("This is the immutable reconciliation snapshot stored when the adjustment was approved.")}</p>`
		: "";

	frappe.msgprint({
		title: result.snapshot ? __("Reconciliation Snapshot") : __("Read-only Reconciliation Preview"),
		indicator: result.verified_hours > 0 ? "green" : "orange",
		message: `${snapshot}<table class="table table-bordered"><tbody>${body}</tbody></table>${warnings}<p class="text-muted">${__("No Salary Slip, Additional Salary, leave, or accounting record was created.")}</p>`,
		wide: true,
	});
}
