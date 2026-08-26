frappe.listview_settings["Overtime Candidate"] = {
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
