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

			const title = "Cambiar estado de la tarea";
			const primary_label = "Cambiar estado";
			const fields = [
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

			function callback({ status }) {
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

			frappe.prompt(fields, callback, title, primary_label);
		}

		request_revision(task_id, callback) {
			const { frm } = this;

			if (!task_id) {
				frappe.throw("Por favor, selecciona una tarea para solicitar revisión.");
			}

			frm.call("request_revision", { task_id }, function() {
				callback && callback(response);
			}, true);
		}

		apply_filters(frm) {
			frm.refresh(); // ToDo: refresh the table instead of the whole form
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

	}
}