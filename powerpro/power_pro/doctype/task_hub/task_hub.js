// Copyright (c) 2025, Yefri Tavarez and contributors
// For license information, please see license.txt

{
	const { datetime: date } = frappe;
	function setup(frm) {
		_disable_save(frm);
	}

	function onload_post_render(frm) {
		_set_defaults(frm);
		_fetch_tasks(frm);
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
	}

	function _disable_save(frm) {
		frm.disable_save();
	}

	frappe.ui.form.on("Task Hub", {
		setup,
		onload_post_render,
	});
}
