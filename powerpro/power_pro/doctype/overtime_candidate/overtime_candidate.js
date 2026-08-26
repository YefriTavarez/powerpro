// Copyright (c) 2026, PowerPro contributors
// For license information, please see license.txt

frappe.ui.form.on("Overtime Candidate", {
	refresh(frm) {
		frm.dashboard.set_headline_alert(
			__("This is a review item only. No payroll or leave document is created by a decision."),
			"blue"
		);
		if (frm.is_new() || ![
			"Open",
			"Eligibility Pending",
			"Needs Check-in Review",
		].includes(frm.doc.status)) {
			return;
		}
		if (!frm.perm?.[0]?.write) {
			return;
		}

		add_decision(frm, __("Approve Cash"), "Approved Cash");
		add_decision(frm, __("Approve Compensatory Rest"), "Approved Compensatory Rest");
		add_decision(frm, __("Reject"), "Rejected");
		add_decision(frm, __("Mark Invalid Check-in"), "Invalid Check-in");
	},
});

function add_decision(frm, label, decision) {
	frm.add_custom_button(label, () => {
		frappe.prompt({
			fieldname: "reason",
			fieldtype: "Small Text",
			label: __("Decision Reason"),
			reqd: 1,
		}, ({ reason }) => {
			frappe.call({
				method: "powerpro.controllers.overtime_candidates.decide_overtime_candidate",
				args: { candidate: frm.doc.name, decision, reason },
				freeze: true,
				freeze_message: __("Saving overtime review decision..."),
			}).then(() => frm.reload_doc());
		}, __("Review Overtime Candidate"));
	}, __("Overtime Review"));
}
