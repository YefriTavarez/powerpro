// Copyright (c) 2025, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.provide("powerpro.masks");

{
	const last_value = {

	};

	function setup(frm) {
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

	function sales_order(frm) {
		frm.set_value("producto", "");
	}

	function _listen_on_all_fields(frm) {
		const { fields } = frm;

		fields
			.map(({ df }) => df)
			.filter(df => !frappe.model.no_value_type.includes(df.fieldtype))
			.map(function({ fieldname }) {
				frappe.ui.form.on(frm.doctype, fieldname, function(frm) {
					if (last_value[fieldname] === frm.doc[fieldname]) {
						return;
					}
					last_value[fieldname] = frm.doc[fieldname];
					_update_project_name({ frm, fieldname });
				});
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
					return `indicator ${indicators[status] || "secondary"}`;
				};

				const table = `
					<table class="table table-zebra">
						<thead>
							<tr style="background-color: var(--control-bg); border-radius: 4px;">
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
													return `<span class="badge badge-info p-2 my-1">${user}</span>`;
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

	// function _set_qty_mask(frm) {
	// 	// function formatNumberInput(input) {
	// 	// 	let value = input.value.replace(/\D/g, ''); // Elimina todo lo que no sea dígito
	// 	// 	value = new Intl.NumberFormat('es-DO').format(value); // Formato latino (puntos para miles)
	// 	// 	input.value = value;
	// 	// }

	// 	// powerpro.masks.formatNumberInput = formatNumberInput;

	// 	const field = frm.get_field("cantidad_a_producir");
	// 	const { $input } = field;
	// 	// field.$input.attr("oninput", "powerpro.masks.formatNumberInput(this)");


	// 	async function formatNumber(value) {
	// 		await frappe.timeout(.1);
	// 		// Elimina todo excepto dígitos y el punto decimal
	// 		value = value.replace(/[^0-9.]/g, '');
	// 		if (!value) return '';

	// 		const parts = value.split('.');
	// 		const integerPart = parts[0];
	// 		const decimalPart = parts[1] || '';

	// 		// Formatea la parte entera al estilo es-DO
	// 		const formattedInt = new Intl.NumberFormat('es-DO').format(Number(integerPart));

	// 		return decimalPart ? `${formattedInt}.${decimalPart}` : formattedInt;
	// 	}

	// 	async function formatNumberInput(input) {
	// 		const cursorPos = input.selectionStart;
	// 		input.value = await formatNumber(input.value);
	// 		// Opcional: restaurar posición del cursor
	// 		input.setSelectionRange(cursorPos, cursorPos);
	// 	}

	// 	// Aplica formato en tiempo real
	// 	$input[0].addEventListener('input', function () {
	// 		formatNumberInput(this);
	// 	});


	// 	// const input = $input[0];
	// 	// input.value = formatNumber(input.value);
	// }

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
			() => {
				const fieldname = "producto";
				const get_query = function () {
					const query = "powerpro.controllers.queries.get_sales_order_items";
					const filters = {
						"sales_order": frm.doc.sales_order || "",
					};

					if (!frm.doc.sales_order) {
						return { filters };
					}

					return { query, filters };
				};

				frm.set_query(fieldname, get_query);
			},
		]);
	}

	frappe.ui.form.on("Project", {
		setup,
		refresh,
		sales_order,
		project_template,
	});
}