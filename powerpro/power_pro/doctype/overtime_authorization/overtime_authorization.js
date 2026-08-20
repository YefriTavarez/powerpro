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
			frm.add_custom_button(__("Reconciliation Preview"), () => {
				frappe.call({
					method: "powerpro.controllers.overtime.get_reconciliation_preview",
					args: { authorization: frm.doc.name },
					freeze: true,
					freeze_message: __("Comparing approval, shift, holiday, and punches..."),
				}).then(({ message }) => show_reconciliation(message));
			}, __("Overtime"));
		}
	},
});

function show_reconciliation(result) {
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

	frappe.msgprint({
		title: __("Read-only Reconciliation Preview"),
		indicator: result.verified_hours > 0 ? "green" : "orange",
		message: `<table class="table table-bordered"><tbody>${body}</tbody></table>${warnings ? `<p><strong>${__("Warnings")}</strong></p><ul>${warnings}</ul>` : ""}<p class="text-muted">${__("No Salary Slip, Additional Salary, leave, or accounting record was created.")}</p>`,
		wide: true,
	});
}
