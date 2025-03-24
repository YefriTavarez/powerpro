// Copyright (c) 2025, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

{
	function refresh(frm) {
		frm.set_df_property("project_docfields", "cannot_add_rows", true);
		frm.set_df_property("project_docfields", "cannot_delete_rows", true);
	}

	frappe.ui.form.on("Project Template", {
		refresh,
	});
}