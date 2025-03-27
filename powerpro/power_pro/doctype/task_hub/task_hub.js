// Copyright (c) 2025, Yefri Tavarez and contributors
// For license information, please see license.txt

{
	const { datetime: date } = frappe;
	function setup(frm) {
		_disable_save(frm);
	}

	function onload_post_render(frm) {
		_set_defaults(frm);
		_render_task_list(frm);
	}

	function _set_defaults(frm) {
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
	}

	function _render_task_list(frm) {
		const field = frm.get_field("hub");

		field
			.$wrapper
			.empty()
			.html(
				frappe.render_template(
					"task_list",
					{
						"tasks": frm.doc.tasks || [],
					}
				)
			)
		;
	}

	function _disable_save(frm) {
		frm.disable_save();
	}

	frappe.ui.form.on("Task Hub", {
		setup,
		onload_post_render,
	});
}
