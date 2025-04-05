// Copyright (c) 2025, Yefri Tavarez and contributors
// For license information, please see license.txt


frappe.provide("powerpro.task_hub");
{
	const { datetime: date } = frappe;
	
	let actions_controller, auto_refresh;
	
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
		
		const filters = {
			"name": doc.task_id,
			"responsible": doc.responsible,
			"project": doc.project,
			"status": doc.status,
			"exp_start_date": doc.exp_start_date,
			"exp_end_date": doc.exp_end_date,
		};

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
		});
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
							return str.charAt(0).toUpperCase() + str.slice(1);
						},
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
						actions_controller.apply_filters(frm);
						break;
					case "reset-filters":
						actions_controller.reset_filters(frm);
						break;
				}
			});

		
		sub_menu.find("input[type=checkbox]")
			.attr("checked", false)
			.change(function() {
				const isChecked = jQuery(this).is(":checked");

				auto_refresh = isChecked;
			});
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
		apply_filters,
		task_id: frm => {
			if (auto_refresh) {
				apply_filters(frm);
			}
		},
		responsible: frm => {
			if (auto_refresh) {
				apply_filters(frm);
			}
		},
		exp_start_date: frm => {
			if (auto_refresh) {
				apply_filters(frm);
			}
		},
		exp_end_date: frm => {
			if (auto_refresh) {
				apply_filters(frm);
			}
		},
		project: frm => {
			if (auto_refresh) {
				apply_filters(frm);
			}
		},
		status: frm => {
			if (auto_refresh) {
				apply_filters(frm);
			}
		},
	});
}
