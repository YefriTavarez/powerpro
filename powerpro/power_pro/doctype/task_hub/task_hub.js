// Copyright (c) 2025, Yefri Tavarez and contributors
// For license information, please see license.txt


frappe.provide("powerpro.task_hub");
{
	const { datetime: date } = frappe;
	
	let actions_controller;

	function setup(frm) {
		_set_queries(frm);
		_disable_save(frm);
		_setup_actions_controller(frm);
	}

	function refresh(frm) {
		// _set_defaults(frm);
		_fetch_tasks(frm);
		_render_task_list(frm);
	}

	function onload_post_render(frm) {
        jQuery(document).ready(function() {
            jQuery('[data-toggle="tooltip"]').tooltip();
        });
	}

	function apply_filters(frm) {
		// read filters from the form
		// request new tasks from backend via frm.call
		// update frm.doc.tasks
		// re-render the task list

		const { doc } = frm;

		// filters:
		// - task_id
		// - responsible
		// - project
		// - status
		// - exp_start_date
		// - exp_end_date

		const filters = {};

		if (doc.task_id) {
			filters.name = doc.task_id;
		}
		if (doc.responsible) {
			filters.responsible = doc.responsible;
		}
		if (doc.project) {
			filters.project = doc.project;
		}
		if (doc.status) {
			filters.status = doc.status;
		}
		if (doc.exp_start_date) {
			filters.exp_start_date = doc.exp_start_date;
		}
		if (doc.exp_end_date) {
			filters.exp_end_date = doc.exp_end_date;
		}
		

		frm.call("fetch_tasks", { filters }, function(response) {
			doc.tasks = response.message;
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
		const { doc } = frm;

		doc.tasks = [];

		const filters = {};

		if (doc.task_id) {
			filters.name = doc.task_id;
		}

		if (doc.responsible) {
			filters.responsible = doc.responsible;
		}

		if (doc.project) {
			filters.project = doc.project;
		}

		if (doc.status) {
			filters.status = doc.status;
		}

		if (doc.exp_start_date) {
			filters.exp_start_date = doc.exp_start_date;
		}

		if (doc.exp_end_date) {
			filters.exp_end_date = doc.exp_end_date;
		}

		frm.call("fetch_tasks", {
			filters,
		}, function(response) {
			doc.tasks = response.message;
			_render_task_list(frm);
		}, true);
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
						"format_date": (date) => {
							return frappe.format(date, {
								fieldtype: "Date",
							});
						},
						"capitalize": (str) => {
							return str.replace("-", " ")
							.split(" ")
							.map((word) => {
								return word.charAt(0).toUpperCase() + word.slice(1);
							})
							.join(" ");

							// return str.charAt(0).toUpperCase() + str.slice(1);
						},
						"icon": frappe.utils.icon,
						"translate": {
							// priorities
							"High": "Alto",
							"Medium": "Medio",
							"Low": "Bajo",
							"Urgent": "Urgente",

							// statuses
							"Open": "Abierto",
							"Working": "Trabajando",
							"Pending Review": "Pendiente de revisión",
							"Overdue": "Vencido",
							"Completed": "Completado",
							"Cancelled": "Cancelado",
						}
					}
				)
			)
		;

		_setup_listeners(frm);
	}

	function _setup_listeners(frm) {
		const { $wrapper: hub } = frm.get_field("hub");
		const { $wrapper: sub_menu } = frm.get_field("sub_menu");
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
		hub.find("a[data-action]")
			.on("click", function (event) {
				event.preventDefault();

				const action = jQuery(this).attr("data-action");
				const task_id = jQuery(this).attr("data-task-id");

				switch (action) {
					case "reopen":
						actions_controller.reopen_task(task_id, _ => apply_filters(frm));
						break;
					case "complete":
						actions_controller.complete_task(task_id, _ => apply_filters(frm));
						break;
					case "change_status":
						actions_controller.change_status(task_id, _ => apply_filters(frm));
						break;
					case "request_revision":
						actions_controller.request_revision(task_id, _ => apply_filters(frm));
						break;
				}
			});

		sub_menu
			.find("button[data-action]")
			.click(function(event) {
				event.preventDefault();

				const action = jQuery(this).attr("data-action");

				switch (action) {
					case "apply-filters":
						apply_filters(frm);
						break;
					case "reset-filters":
						actions_controller.reset_filters(frm, _ => apply_filters(frm));
						break;
				}
			});

		
		// sub_menu.find("input[type=checkbox]")
		// 	.change(function() {
		// 		const isChecked = jQuery("this").is(":checked");

		// 		auto_refresh = isChecked;
		// 	});
	}

	function _set_queries(frm) {
		frappe.run_serially([
			() => {
				frm.set_query("task_id", function() {
					return {
						filters: {
							"is_template": 0,
						},
					};
				});
			},
		]);
	}

	function _disable_save(frm) {
		frm.disable_save();
	}

	function _setup_actions_controller(frm) {
		actions_controller = new powerpro.task_hub.ActionsController(frm);
	}

	frappe.ui.form.on("Task Hub", {
		setup,
		refresh,
		onload_post_render,
		apply_filters,
		task_id: frm => {
			const auto_refresh = jQuery("#auto-refresh")
				.is(":checked")
				;

			if (auto_refresh) {
				apply_filters(frm);
			}
		},
		responsible: frm => {
			const auto_refresh = jQuery("#auto-refresh")
				.is(":checked")
				;

			if (auto_refresh) {
				apply_filters(frm);
			}
		},
		exp_start_date: frm => {
			const auto_refresh = jQuery("#auto-refresh")
				.is(":checked")
				;

			if (auto_refresh) {
				apply_filters(frm);
			}
		},
		exp_end_date: frm => {
			const auto_refresh = jQuery("#auto-refresh")
				.is(":checked")
				;

			if (auto_refresh) {
				apply_filters(frm);
			}
		},
		project: frm => {
			const auto_refresh = jQuery("#auto-refresh")
				.is(":checked")
				;

			if (auto_refresh) {
				apply_filters(frm);
			}
		},
		status: frm => {
			const auto_refresh = jQuery("#auto-refresh")
				.is(":checked")
				;

			if (auto_refresh) {
				apply_filters(frm);
			}
		},
	});
}
