// Copyright (c) 2025, Yefri Tavarez and contributors
// For license information, please see license.txt

{
	const { datetime: date } = frappe;
	function setup(frm) {
		_disable_save(frm);
	}

	function refresh(frm) {
		_set_defaults(frm);
		_fetch_tasks(frm);
		_render_task_list(frm);
	}

	function apply_filters(frm) {
		// read filters from the form
		// request new tasks from backend via frm.call
		// update frm.doc.tasks
		// re-render the task list

		const { doc } = frm;

		// filters:
		// - responsible
		// - project
		// - status
		// - exp_start_date
		// - exp_end_date
		
		const filters = {
			"responsible": doc.responsible,
			"project": doc.project,
			"status": doc.status,
			"exp_start_date": doc.exp_start_date,
			"exp_end_date": doc.exp_end_date,
		};

		frm.call("fetch_tasks", { filters }, function(response) {
			frm.doc.tasks = response.message;
			_render_task_list(frm);
		});
	}

	function _set_defaults(frm) {
		const { doc } = frm;

		if (!doc.responsible) {
			frm.set_value("responsible", frappe.session.user);
		}

		if (!doc.exp_start_date) {
			frm.set_value("exp_start_date", date.nowdate());
		}

		if (!doc.exp_end_date) {
			frm.set_value("exp_end_date", date.add_days(doc.exp_start_date, 30));
		}
	}

	function _fetch_tasks(frm) {
		frm.doc.tasks = [
			{
				id: 'TASK-001',
				title: 'Revisar el reporte mensual de actividades y generar un resumen ejecutivo para la junta directiva',
				project: 'PROY-0001',
				due_date: '2025-03-30',
				status: 'open',
				user: 'Juan Pérez',
			},
			{
				id: 'TASK-002',
				title: 'Actualizar toda la documentación técnica del proyecto para cumplir con los estándares de calidad',
				project: 'PROY-0002',
				due_date: '2025-03-25',
				status: 'overdue',
				user: 'María López',
			},
			{
				id: 'TASK-003',
				title: 'Preparar una presentación detallada para el cliente sobre los avances del proyecto y próximos pasos',
				project: 'PROY-0003',
				due_date: '2025-03-28',
				status: 'completed',
				user: 'Carlos Gómez',
			},
			{
				id: 'TASK-004',
				title: 'Realizar un análisis de impacto de los cambios en el alcance del proyecto y presentar recomendaciones',
				project: 'PROY-0004',
				due_date: '2025-03-30',
				status: 'open',
				user: 'Ana Ramírez',
			},
			{
				id: 'TASK-005',
				title: 'Coordinar una reunión de revisión de entregables con el equipo de trabajo',
				project: 'PROY-0005',
				due_date: '2025-03-29',
				status: 'open',
				user: 'Pedro Jiménez',
			},
		];
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
						"capitalize": (str) => {
							return str.charAt(0).toUpperCase() + str.slice(1);
						},
					}
				)
			)
		;

		_setup_listeners(frm);
	}

	function _setup_listeners(frm) {
		// jQuery("#toggleViewButton").on("click", function () {
		// 	const tableView = jQuery("#tableView");
		// 	const postView = jQuery("#postView");

		// 	if (tableView.hasClass("d-block")) {
		// 		tableView.removeClass("d-block").addClass("d-none");
		// 		postView.removeClass("d-none").addClass("d-block");
		// 	} else {
		// 		tableView.removeClass("d-none").addClass("d-block");
		// 		postView.removeClass("d-block").addClass("d-none");
		// 	}
		// });

		// action buttons
		// data-action="reopen"
		// data-action="complete"
		// data-action="change_status"
		// data-action="request_revision"
		//
		jQuery("a[data-action]").on("click", function (event) {
			event.preventDefault();

			const action = jQuery(this).attr("data-action");
			const task_id = jQuery(this).attr("data-task-id");

			switch (action) {
				case "reopen":
					_reopen_task(frm, task_id);
					break;
				case "complete":
					_complete_task(frm, task_id);
					break;
				case "change_status":
					_change_status(frm, task_id);
					break;
				case "request_revision":
					_request_revision(frm, task_id);
					break;
			}
		});
	}

	function _disable_save(frm) {
		frm.disable_save();
	}

	frappe.ui.form.on("Task Hub", {
		setup,
		refresh,
		apply_filters,
	});
}
