// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

{
	function refresh(frm) {
		frappe.msgprint("Hello World!");
	}

	frappe.ui.form.on("Item Color", {
		refresh,
	});
}