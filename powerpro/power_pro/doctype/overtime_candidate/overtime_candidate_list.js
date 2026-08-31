frappe.listview_settings["Overtime Candidate"] = {
	onload(listview) {
		if (!can_refresh_candidates()) {
			return;
		}
		listview.page.add_inner_button(
			__("Refresh from Check-ins"),
			() => show_refresh_dialog(listview),
			__("Overtime Tools")
		);
	},

	get_indicator(doc) {
		const colors = {
			"Open": "blue",
			"Eligibility Pending": "orange",
			"Needs Check-in Review": "yellow",
			"Approved Cash": "green",
			"Approved Compensatory Rest": "green",
			"Rejected": "red",
			"Invalid Check-in": "gray",
			"Superseded": "gray",
		};
		return [__(doc.status), colors[doc.status] || "gray", `status,=,${doc.status}`];
	},
};

function can_refresh_candidates() {
	return ["HR Manager", "Manufacturing Manager", "System Manager"].some(
		(role) => (frappe.user_roles || []).includes(role)
	);
}

function show_refresh_dialog(listview) {
	const yesterday = frappe.datetime.add_days(frappe.datetime.get_today(), -1);
	frappe.prompt([
		{
			fieldname: "company",
			fieldtype: "Link",
			options: "Company",
			label: __("Company"),
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "from_date",
			fieldtype: "Date",
			label: __("From Date"),
			default: yesterday,
			reqd: 1,
		},
		{
			fieldname: "to_date",
			fieldtype: "Date",
			label: __("To Date"),
			default: yesterday,
			reqd: 1,
		},
	], (values) => {
		preview_candidate_refresh(listview, values);
	}, __("Refresh Overtime Candidates"), __("Preview Changes"));
}

function preview_candidate_refresh(listview, values) {
	return run_candidate_refresh(values, true).then(({ message }) => {
		const summary = candidate_refresh_summary(message, true);
		const change_count = ["created", "updated", "invalidated", "superseded"]
			.reduce((total, fieldname) => total + (message[fieldname] || 0), 0);
		if (!change_count) {
			frappe.msgprint({
				title: __("No Candidate Changes"),
				message: summary,
				indicator: "blue",
			});
			return;
		}

		frappe.confirm(
			`${summary}<br><br>${__("Apply these changes to reviewable candidates?")}`,
			() => apply_candidate_refresh(listview, values)
		);
	});
}

function apply_candidate_refresh(listview, values) {
	return run_candidate_refresh(values, false).then(({ message }) => {
		frappe.msgprint({
			title: __("Overtime Candidates Refreshed"),
			message: candidate_refresh_summary(message, false),
			indicator: "green",
		});
		listview.refresh();
	});
}

function run_candidate_refresh(values, dry_run) {
	return frappe.call({
		method: "powerpro.controllers.overtime_candidates.generate_overtime_candidates",
		args: {
			company: values.company,
			from_date: values.from_date,
			to_date: values.to_date,
			dry_run: dry_run ? 1 : 0,
			invalidate_stale: 1,
		},
		freeze: true,
		freeze_message: dry_run
			? __("Previewing corrected Employee Checkins...")
			: __("Refreshing overtime candidates..."),
	});
}

function candidate_refresh_summary(message, preview) {
	const label = (future, completed) => preview ? future : completed;
	return [
		__("Company: {0}", [message.company]),
		__("Date range: {0} to {1}", [message.from_date, message.to_date]),
		__(label("Would create: {0}", "Created: {0}"), [message.created || 0]),
		__(label("Would update: {0}", "Updated: {0}"), [message.updated || 0]),
		__(label("Would invalidate: {0}", "Invalidated: {0}"), [message.invalidated || 0]),
		__(label("Would supersede: {0}", "Superseded: {0}"), [message.superseded || 0]),
		__("Unchanged: {0}", [message.unchanged || 0]),
		__("Skipped because overtime already exists: {0}", [message.skipped_existing_overtime || 0]),
	].join("<br>");
}
