// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.listview_settings["Quality Procedure"] = {
	hide_name_column: true,
	filters: [["status", "!=", "Superseded"]],
	// filters: [["disabled", "=", "0"]],'
	get_indicator(doc) {
		// Draft
		// In Review
		// Approved
		// Published
		// In Revision
		// Obsolete
		// Under Validation
		// Rejected
		// Pending Approval
		// Archived
		// Superseded
		// Cancelled
		const status = doc.status;
		const color = {
			"Draft": "red",
			"In Review": "orange",
			"Approved": "green",
			"Published": "green",
			"In Revision": "orange",
			"Obsolete": "red",
			"Under Validation": "orange",
			"Rejected": "red",
			"Pending Approval": "orange",
			"Archived": "red",
			"Superseded": "red",
			"Cancelled": "red",
		}[status];

		return [status, color, `status,=,${status}`];
	},

};