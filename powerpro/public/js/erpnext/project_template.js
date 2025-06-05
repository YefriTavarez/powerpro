// Copyright (c) 2025, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

{
	function refresh(frm) {
		_set_queries(frm);
		_add_custom_buttons(frm);
		_setup_docfields_table_as_readonly(frm);
	}

	function onload(frm) {
		_dirty_form_if_new_docfields(frm);
	}

	function _set_queries(frm) {
		// Set query for the "user" under the tasks table
		frm.set_query("user", "tasks", function(_, doctype, name) {
			const doc = frappe.get_doc(doctype, name);

			const query = "powerpro.controllers.queries.get_active_users_in_department";
			const filters = {
				department: doc.department,
			};

			return { query, filters };
		});
	}

	function _add_custom_buttons(frm) {
		// const actions_parent = __("Actions");
		const docfields_parent = __("DocFields");

		frappe.run_serially([
			() => {
				const label = __("Syncronizar");
				const action = () => {
					const method = "set_project_docfields";
					const args = {
						for_reload: true,
						with_memory: true
					};
					function callback(response) {
						frappe.show_alert({
							message: __("Campos de projecto sincronizados"),
							indicator: "green",
						});
					}

					frm.call(method, args, callback);
				};

				frm.add_custom_button(label, action, docfields_parent);
			},
			() => {
				const label = __("Resetear");
				const action = () => {
					frappe.confirm(
						__("¿Estás seguro de que deseas resetear los campos de proyecto?"),
						() => _reset_project_docfields(frm), () => {
							frappe.show_alert({
								message: __("Operación cancelada"),
								indicator: "red",
							});
						}
					);
				};

				frm.add_custom_button(label, action, docfields_parent);
			},
		]);
	}

	function _reset_project_docfields(frm) {
		const { doc } = frm;
		for (
			const child of doc.project_docfields
		) {
			child.hidden = false;
			child.reqd = false;
			child.read_only = false;
		}

		frappe.run_serially([ frm.dirty.bind(frm), frm.save.bind(frm) ]);
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