// Copyright (c) 2025, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

{
	function refresh(frm) {
		_setup_docfields_table_as_readonly(frm);
	}

	function onload(frm) {
		_dirty_form_if_new_docfields(frm);
	}

	function _setup_docfields_table_as_readonly(frm) {
		frm.set_df_property("project_docfields", "cannot_add_rows", true);
		frm.set_df_property("project_docfields", "cannot_delete_rows", true);
	}

	function _dirty_form_if_new_docfields(frm) {
		const { doc } = frm;

		const any = doc
			.project_docfields
			.filter(d => d.__islocal)
			.length
		;

		if (any) {
			frm.dirty();
		}
	}

	frappe.ui.form.on("Project Template", {
		refresh,
		onload,
	});
}