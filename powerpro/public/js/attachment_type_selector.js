// Copyright (c) 2025, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.provide("powerpro.utils");
powerpro.utils.select_attachment_type = function(doctype, docname, callback) {
	// Create a dialog to select the attachment type
	const dialog = new frappe.ui.Dialog({
		title: "Seleccionar Tipo de Adjunto",
		fields: [
			{
				fieldtype: "Link",
				fieldname: "attachment_type",
				label: "Tipo de Adjunto",
				options: "Attachment Type",
				get_query() {
					const filters = [
						["Attachment DocTypes", "allow_on_doctype", "=", doctype],
					];
					return { filters };
				},
				reqd: 1,
			},
		],
		primary_action_label: __("Next"),
		primary_action(values) {
			dialog.hide();
			const attachment_type = values.attachment_type;
			callback(attachment_type);
		},
	});

	dialog.show();
};