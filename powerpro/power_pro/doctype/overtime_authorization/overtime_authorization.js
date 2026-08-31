// Copyright (c) 2026, PowerPro contributors
// For license information, please see license.txt

frappe.ui.form.on("Overtime Authorization", {
	refresh(frm) {
		if (frm.doc.docstatus === 0) {
			frm.dashboard.set_headline_alert(
				__("This is only a request until it is submitted before the authorized work begins."),
				"orange"
			);
		}

		if (frm.doc.docstatus === 1) {
			add_settlement_actions(frm);
			frm.add_custom_button(__("Reconciliation Preview"), () => {
				frappe.call({
					method: "powerpro.controllers.overtime.get_reconciliation_preview",
					args: { authorization: frm.doc.name },
					freeze: true,
					freeze_message: __("Comparing approval, shift, holiday, and punches..."),
				}).then(({ message }) => show_reconciliation(frm, message));
			}, __("Overtime"));
		}
	},
});

function add_settlement_actions(frm) {
	const references = parse_json_list(frm.doc.settlement_references);
	references.forEach((reference) => {
		frm.add_custom_button(__("Open {0}", [reference]), () => {
			const doctype = reference === frm.doc.compensatory_credit
				? "Overtime Compensatory Credit"
				: reference === frm.doc.leave_allocation
					? "Leave Allocation"
					: "Additional Salary";
			frappe.set_route("Form", doctype, reference);
		}, __("Settlement"));
	});

	if (["Created", "Paid", "Credited", "Cancelled"].includes(frm.doc.settlement_status)) {
		return;
	}
	frm.add_custom_button(__("Preview and Settle"), () => {
		if (frm.doc.planned_settlement === "Cash") {
			show_payroll_date_dialog(frm);
			return;
		}
		preview_settlement(frm, null);
	}, __("Settlement"));
}

function show_payroll_date_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Cash Settlement Payroll Date"),
		fields: [{
			fieldname: "payroll_date",
			fieldtype: "Date",
			label: __("Payroll Date"),
			reqd: 1,
			default: frappe.datetime.get_today(),
		}],
		primary_action_label: __("Preview"),
		primary_action(values) {
			dialog.hide();
			preview_settlement(frm, values.payroll_date);
		},
	});
	dialog.show();
}

function preview_settlement(frm, payroll_date) {
	frappe.call({
		method: "powerpro.controllers.overtime_settlement.preview_overtime_settlement",
		args: { authorization: frm.doc.name, payroll_date },
		freeze: true,
		freeze_message: __("Calculating the settlement preview..."),
	}).then(({ message }) => show_settlement_preview(frm, message, payroll_date));
}

function show_settlement_preview(frm, result, payroll_date) {
	const is_cash = result.method === "Cash";
	const rows = is_cash
		? [
			[__("Payroll Date"), result.payroll_date],
			[__("Hourly Rate"), format_currency(result.hourly_rate, result.currency)],
			[__("Total Amount"), format_currency(result.total_amount, result.currency)],
		]
		: [
			[__("Banked Hours"), format_number(result.current_hours)],
			[__("Leave Days Added Now"), format_number(result.days_to_credit)],
			[__("Residual Hours"), format_number(result.residual_hours)],
			[__("Leave Period"), result.leave_period],
			[__("Leave Allocation"), result.leave_allocation || __("Will be created when days are available")],
		];
	const body = rows.map(([label, value]) => `
		<tr><td>${escape_html(label)}</td><td class="text-right">${escape_html(value)}</td></tr>
	`).join("");
	let dialog;
	dialog = frappe.msgprint({
		title: __("Overtime Settlement Preview"),
		message: `<table class="table table-bordered"><tbody>${body}</tbody></table>
			<p class="text-muted">${__("Nothing has been created yet. Confirm to freeze this settlement.")}</p>`,
		wide: true,
		primary_action: {
			label: is_cash ? __("Create Additional Salary") : __("Credit Compensatory Rest"),
			action() {
				dialog.hide();
				frappe.call({
					method: "powerpro.controllers.overtime_settlement.settle_overtime_authorization",
					args: { authorization: frm.doc.name, payroll_date },
					freeze: true,
					freeze_message: __("Creating the audited overtime settlement..."),
				}).then(() => frm.reload_doc());
			},
		},
	});
}

function parse_json_list(value) {
	if (!value) return [];
	try {
		const parsed = JSON.parse(value);
		return Array.isArray(parsed) ? parsed : [];
	} catch (error) {
		return [];
	}
}

function escape_html(value) {
	return frappe.utils.escape_html(String(value ?? ""));
}

function format_number(value) {
	return Number(flt(value || 0, 4)).toFixed(4);
}

function show_reconciliation(frm, result) {
	const rows = [
		[__("Classification"), result.classification],
		[__("Verified hours"), result.verified_hours],
		[__("Regular overtime +35%"), result.regular_35_hours],
		[__("Regular overtime +100%"), result.regular_100_hours],
		[__("Legal holiday +100%"), result.holiday_100_hours],
		[__("Weekly rest"), result.weekly_rest_hours],
		[__("Night hours"), result.night_hours],
	];
	const body = rows
		.map(([label, value]) => `<tr><td>${frappe.utils.escape_html(String(label))}</td><td class="text-right">${frappe.utils.escape_html(String(value))}</td></tr>`)
		.join("");
	const warnings = (result.warnings || [])
		.map((warning) => `<li>${frappe.utils.escape_html(String(warning))}</li>`)
		.join("");

	const options = {
		title: __("Read-only Reconciliation Preview"),
		indicator: result.verified_hours > 0 ? "green" : "orange",
		message: `<table class="table table-bordered"><tbody>${body}</tbody></table>${warnings ? `<p><strong>${__("Warnings")}</strong></p><ul>${warnings}</ul>` : ""}<p class="text-muted">${__("No Salary Slip, Additional Salary, leave, or accounting record was created.")}</p>`,
		wide: true,
	};
	let dialog;
	if (
		!frm.doc.overtime_work_call
		&& result.reconciliation_status !== "Scheduled"
		&& !["Created", "Paid", "Credited"].includes(frm.doc.settlement_status)
	) {
		options.primary_action = {
			label: __("Save Attendance Snapshot"),
			action() {
				dialog.hide();
				frappe.call({
					method: "powerpro.controllers.overtime.save_authorization_reconciliation",
					args: { authorization: frm.doc.name },
					freeze: true,
					freeze_message: __("Saving verified attendance and adherence..."),
				}).then(() => frm.reload_doc());
			},
		};
	}
	dialog = frappe.msgprint(options);
}
