// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on("DGII Payroll Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Preview Overtime Candidates"), () => {
			run_candidate_scan(true);
		}, __("Overtime Candidates"));

		if (frm.doc.enable_overtime_candidate_generation) {
			frm.add_custom_button(__("Generate Overtime Candidates Now"), () => {
				frappe.confirm(
					__("Generate or refresh review-only candidates now? No payroll or leave documents will be created."),
					() => run_candidate_scan(false)
				);
			}, __("Overtime Candidates"));
		}
	},

	enable_overtime_candidate_generation(frm) {
		if (!frm.doc.enable_overtime_candidate_generation) {
			return;
		}
		if (!frm.doc.overtime_candidate_threshold_minutes) {
			frm.set_value("overtime_candidate_threshold_minutes", 15);
		}
		if (!frm.doc.overtime_candidate_lookback_days) {
			frm.set_value("overtime_candidate_lookback_days", 2);
		}
		if (!frm.doc.overtime_candidate_designation_keywords) {
			frm.set_value(
				"overtime_candidate_designation_keywords",
				"Operador\nAuxiliar\nMecánico\nElectricista\nInspector\nPrensista\nTroquelador"
			);
		}
	},
});

function run_candidate_scan(dry_run) {
	return frappe.call({
		method: "powerpro.controllers.overtime_candidates.generate_overtime_candidates",
		args: { dry_run: dry_run ? 1 : 0 },
		freeze: true,
		freeze_message: __("Reviewing completed Employee Checkins..."),
	}).then(({ message }) => {
		const action_label = (future, completed) => dry_run ? future : completed;
		const summary = [
			__("Candidates found: {0}", [message.candidate_count || 0]),
			__(action_label("Would create: {0}", "Created: {0}"), [message.created || 0]),
			__(action_label("Would update: {0}", "Updated: {0}"), [message.updated || 0]),
			__("Unchanged: {0}", [message.unchanged || 0]),
			__("Skipped because overtime already exists: {0}", [message.skipped_existing_overtime || 0]),
		].join("<br>");
		frappe.msgprint({
			title: dry_run ? __("Overtime Candidate Preview") : __("Overtime Candidates Updated"),
			message: summary,
			indicator: "blue",
		});
		if (!dry_run) {
			frappe.set_route("List", "Overtime Candidate");
		}
	});
}
