// Copyright (c) 2025, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.provide("powerpro.masks");

{
	let form;
	const last_value = {

	};

	function setup(frm) {
		form = frm; 
		frappe.require([
			"/assets/powerpro/css/erpnext/project.css",
		]);

		_listen_on_all_fields(frm);
	}

	function refresh(frm) {
		// _set_qty_mask(frm);
		_set_queries(frm);
		_render_docfields(frm);
		_render_related_tasks(frm);
	}

	function project_template(frm) {
		_render_docfields(frm);
	}

	const listen_on_field = function(frm, fieldname) {
		frappe.ui.form.on(frm.doctype, fieldname, frappe.utils.debounce(function(frm) {
			if (last_value[fieldname] === frm.doc[fieldname]) {
				return;
			}
			last_value[fieldname] = frm.doc[fieldname];
			_update_project_name({ frm, fieldname });
		}), 1000);
	}

	function _listen_on_all_fields(frm) {
		const { fields } = frm;

		fields
			.map(({ df }) => df)
			.filter(df => !frappe.model.no_value_type.includes(df.fieldtype))
			.map(function({ fieldname }) {
				return listen_on_field(frm, fieldname);
			});
	}

	function _render_related_tasks(frm) {
		// const { doc } = frm;

		frm.call("get_related_tasks", { /* no args */ }, function({ message: tasks }) {
				console.log({ tasks})
				const $wrapper = frm.get_field("task_display").$wrapper;
				$wrapper.empty();

				if (!tasks || tasks.length === 0) {
					$wrapper.html("<p>Nada para mostrar</p>");
					return;
				}

				const task_count = tasks.length;
				const task_text = task_count > 1 ? "Tareas" : "Tarea";
				const task_count_text = `<h3>${task_count} ${task_text} relacionadas</h5>`;
				$wrapper.empty();
				$wrapper.append(task_count_text);
				$wrapper.append("<hr>");

				const translated_status = {
					"Open": "Abierto",
					"Working": "En progreso",
					"Pending Review": "Pendiente de revisión",
					"Overdue": "Vencido",
					"Completed": "Completado",
					"Cancelled": "Cancelado",
				};

				const indicators = {
					"Open": "orange",
					"Working": "blue",
					"Pending Review": "yellow",
					"Overdue": "red",
					"Completed": "green",
					"Cancelled": "gray",
				};
				const status_class = (status) => {
					return `indicator-pill ${indicators[status] || "secondary"}`;
				};

				const table = `
					<style>
						.table-zebra tbody tr:nth-of-type(odd) {
							background-color: #ffffff;
						}
						.table-zebra tbody tr:nth-of-type(even) {
							background-color: #fafafa;
						}
					</style>
					<table class="table table-zebra">
						<thead>
							<tr style="background-color: #021e42; color: white; border-radius: 4px;">
								<th>
								<span style="font-size: 1.2em">Tarea</span>
								</th>
								<th>
								<span style="font-size: 1.2em">Estado</span>
								</th>
								<th>
								<span style="font-size: 1.2em">Usuarios</span>
								</th>
							</tr>
						</thead>
						<tbody>
							${(tasks || []).map(
								({ name, subject, status, users }) => `
									<tr>
										<td>
											<a title="${name}" href="/app/task/${name}" target="_blank">
												${name.split("-").pop()}: ${subject}
											</a>
										</td>
										<td>
											<span class="indicator ${status_class(status)}">
												${translated_status[status] || status}
											</span>
										</td>
										<td>
											${cstr(users || "N/A").split("<br>")
												.map((user) => {
													return `<span class="badge badge-light p-2 my-1">${user}</span>`;
												})
												.join("<br> ")}
										</td>
									</tr>
								`).join("") || "<tr><td colspan='3'>No hay tareas relacionadas</td></tr>"}
						</tbody>
					</table>
				`;

				$wrapper.append(table);
			});
	}

	function _render_docfields(frm) {
		const { doc } = frm;

		// if (!doc.project_template) {
		// 	return ; // Do nothing
		// }

		frappe.call({
			method: "powerpro.controllers.project_template.get_project_docfields",
			args: {
				"project_template_id": frm.doc.project_template,
			},
			callback({ message: docfields }) {
				for (const docfield of docfields) {
					const { fieldname, read_only, reqd, hidden, set_only_once } = docfield;

					for (
						const { property, value } of [
							{ property: "read_only", value: read_only },
							{ property: "reqd", value: reqd },
							{ property: "hidden", value: hidden },
							{ property: "set_only_once", value: set_only_once },
						]
					) {
						frm.set_df_property(fieldname, property, value);
					}
				}
			},
		});
	}

	function _update_project_name({
		frm,
		fieldname = null,
		for_validate = false,
	} = {}) {
		const { doc }  = frm;

		if (!doc[fieldname]) {
			// ToDo: Remove this
		}

		frm.call("render_project_name", { for_validate }, function() {
			if (!for_validate) {
				frm.dirty();
			}
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

	frappe.realtime.on("attachment_upload_completed", function(data) {
		// const { doc } = form;
		if (form.doc.__unsaved) {
			form.dashboard.clear_headline();
			form.dashboard.set_headline_alert(
				__("This form has been modified after you have loaded it") +
					'<button class="btn btn-xs btn-primary pull-right" onclick="cur_frm.reload_doc()">' +
					__("Refresh") +
					"</button>",
				"alert-warning"
			);
		} else {
			form.debounced_reload_doc();
		}
	});

	frappe.ui.form.on("Project", {
		setup,
		refresh,
		project_template,
	});
}