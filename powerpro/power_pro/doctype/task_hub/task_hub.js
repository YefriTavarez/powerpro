// Copyright (c) 2025, Yefri Tavarez and contributors
// For license information, please see license.txt

{
	const { datetime: date } = frappe;
	function onload_post_render(frm) {
		const { doc } = frm;

		if (!doc.responsible) {
			frm.set_value("responsible", frappe.session.user);
		}

		if (!doc.from_date) {
			frm.set_value("from_date", date.nowdate());
		}

		if (!doc.to_date) {
			frm.set_value("to_date", date.add_days(doc.from_date, 30));
		}

		frm.disable_save();
	}

	frappe.ui.form.on("Task Hub", {
		onload_post_render,
	});
}
