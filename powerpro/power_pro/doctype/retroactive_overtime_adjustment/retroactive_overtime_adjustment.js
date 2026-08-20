// Copyright (c) 2026, PowerPro contributors
// For license information, please see license.txt

frappe.ui.form.on("Retroactive Overtime Adjustment", {
	refresh(frm) {
		if (frm.doc.docstatus === 0) {
			frm.dashboard.set_headline_alert(
				__("Historical overtime is an audited exception and requires existing Employee Checkin evidence."),
				"orange"
			);
		}

		if (!frm.is_new() && frm.doc.docstatus < 2) {
			const label = frm.doc.docstatus === 1
				? __("Reconciliation Snapshot")
				: __("Preview Reconciliation");
			frm.add_custom_button(label, () => {
				frappe.call({
					method: "powerpro.controllers.overtime.get_retroactive_adjustment_preview",
					args: { adjustment: frm.doc.name },
					freeze: true,
					freeze_message: __("Comparing historical approval, shift, holiday, and punches..."),
				}).then(({ message }) => show_retroactive_reconciliation(message));
			}, __("Overtime"));
		}
	},
});

function show_retroactive_reconciliation(result) {
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
		.filter(Boolean)
		.map((warning) => `<li>${frappe.utils.escape_html(String(warning))}</li>`)
		.join("");
	const snapshot = result.snapshot
		? `<p class="text-muted">${__("This is the immutable reconciliation snapshot stored when the adjustment was approved.")}</p>`
		: "";

	frappe.msgprint({
		title: result.snapshot ? __("Reconciliation Snapshot") : __("Read-only Reconciliation Preview"),
		indicator: result.verified_hours > 0 ? "green" : "orange",
		message: `${snapshot}<table class="table table-bordered"><tbody>${body}</tbody></table>${warnings ? `<p><strong>${__("Warnings")}</strong></p><ul>${warnings}</ul>` : ""}<p class="text-muted">${__("No Salary Slip, Additional Salary, leave, or accounting record was created.")}</p>`,
		wide: true,
	});
}
