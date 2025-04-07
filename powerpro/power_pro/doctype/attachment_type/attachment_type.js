// Copyright (c) 2025, Yefri Tavarez and contributors
// For license information, please see license.txt

{
	function refresh(frm) {
		_set_queries(frm);
	}

	function _set_queries(frm) {
		frappe.run_serially([
			_ => {
				// set attachment_doctypes query
				frm.set_query("attachment_doctypes", () => {
					return {
						filters: {
							istable: false,
						},
					};
				});
			},
		]);
	}

	frappe.ui.form.on("Attachment Type", {
		refresh,
	});
}