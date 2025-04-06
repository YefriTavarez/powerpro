// Copyright (c) 2025, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

{
	frappe.provide("powerpro.task_hub");

	powerpro.task_hub.ActionsController = class {
		constructor(frm) {
			this.frm = frm;
		}

		reopen_task(task_id, callback) {
			const { frm } = this;

			if (!task_id) {
				frappe.throw("Por favor, selecciona una tarea para reabrir.");
			}

			frm.call("reopen_task", { task_id }, function(response) {
				callback && callback(response);
			}, true);
		}

		complete_task(task_id, callback) {
			const { frm } = this;

			if (!task_id) {
				frappe.throw("Por favor, selecciona una tarea para completar.");
			}

			frm.call("complete_task", { task_id }, function(response) {
				callback && callback(response);
			}, true);
		}

		change_status(task_id, callback) {
			const { frm } = this;

			if (!task_id) {
				frappe.throw("Por favor, selecciona una tarea para cambiar el estado.");
			}

			const title = `${task_id}: Cambiar estado de la Tarea`;
			const current_status = {
				"open": "Abierto",
				"working": "En progreso",
				"pending-review": "Pendiente de revisión",
				"overdue": "Vencido",
				"completed": "Completado",
				"cancelled": "Cancelado",
			}[
				jQuery(`tr[data-task-id="${task_id}"]`)
					.attr("data-status")
			];
			
			const primary_label = "Cambiar estado";
			const fields = [
				{
					fieldname: "current_status",
					fieldtype: "Data",
					label: "Estado actual",
					read_only: 1,
					default: current_status,
					placeholder: current_status,
				},
				{
					fieldname: "status",
					fieldtype: "Select",
					label: "Nuevo estado",
					options: [
						"Open",
						"Working",
						"Pending Review",
						"Overdue",
						"Completed",
						"Cancelled",
					],
					reqd: 1,
				},
			];

			function on_dialog_close({ status }) {
				if (status) {
					frm.call("change_status", { task_id, status }, function(response) {
						callback && callback(response);
					}, true);
				} else {
					frappe.show_alert({
						message: `Estado no válido ${status}... no se han realizado cambios.`,
						indicator: "red",
					});
				}
			}

			frappe.prompt(fields, on_dialog_close, title, primary_label);
		}

		request_revision(task_id, callback) {
			const { frm } = this;

			if (!task_id) {
				frappe.throw("Por favor, selecciona una tarea para solicitar revisión.");
			}

			frm.call("request_revision", { task_id }, function(response) {
				callback && callback(response);
			}, true);
		}

		reset_filters(frm, callback) {
			const { doc } = frm;
			// Reset filters to null
			for (const fieldname of ["task_id", "responsible", "project", "status", "exp_start_date", "exp_end_date"]) {
				doc[fieldname] = null;
				frm.refresh_field(fieldname);
			}

			callback && callback();
		}

		open_task_in_window(task_id, callback) {
			const { frm } = this;

			if (!task_id) {
				frappe.throw("Por favor, selecciona una tarea para abrir.");
			}

			const wd = window.open(
				`/app/task/${task_id}`,
				"_blank"
			);

			if (wd) {
				// Browser has allowed it to be opened
				wd.focus();
			} else {
				// Browser has blocked it
				frappe.msgprint(__("Please allow popups for this site"));
			}

			// on close, execute callback
			$(wd).on("unload", function() {
				callback && callback();
			});
		}


		open_project_in_window(project_id, callback) {
			const { frm } = this;

			if (!project_id) {
				frappe.throw("Por favor, selecciona un proyecto para abrir.");
			}

			const wd = window.open(
				`/app/project/${project_id}`,
				"_blank"
			);

			if (wd) {
				// Browser has allowed it to be opened
				wd.focus();
			} else {
				// Browser has blocked it
				frappe.msgprint(__("Please allow popups for this site"));
			}

			// on close, execute callback
			$(wd).on("unload", function() {
				callback && callback();
			});
		}
	}
}