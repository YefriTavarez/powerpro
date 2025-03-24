// Copyright (c) 2025, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */


{
	function refresh(frm) {
		_set_queries(frm);
		_render_docfields(frm);
	}

	function project_template(frm) {
		_render_docfields(frm);
	}


	function _render_docfields(frm) {
		const { doc } = frm;

		// if (!doc.project_template) {
		// 	return ; // Do nothing
		// }

		frappe.call({
			method: "powerpro.controllers.project_template.get_project_docfields",
			args: {
				"project_template_id": cur_frm.doc.project_template,
			},
			callback({ message: docfields }) {
				for (const docfield of docfields) {
					const { fieldname, read_only, reqd, hidden } = docfield;

					for (
						const { property, value } of [
							{ property: "read_only", value: read_only },
							{ property: "reqd", value: reqd },
							{ property: "hidden", value: hidden },
						]
					) {
						frm.set_df_property(fieldname, property, value);
					}
				}
			},
		});
	}

	function _set_queries(frm) {
		frappe.run_serially([
			() => {
				const fieldname = "project_template";
				const get_query = function () {
					const filters = {
						"project_type": frm.doc.project_type || "",
					};

					return { filters };
				};

				frm.set_query(fieldname, get_query);
			},
		]);
	}

	frappe.ui.form.on("Project", {
		refresh,
		project_template,
	});
}