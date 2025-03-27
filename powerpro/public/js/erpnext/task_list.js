// Copyright (c) 2025, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.listview_settings['Task'] = {
	onload(listview) {
		listview.page.add_action_item("Assignar", function() {
			// validate the status of all selected tasks
			// all of them must have one of the following statuses:
			// - Open
			// - Working
			// - Overdue
			// - Pending Review ?

			const task_list = listview.get_checked_items();
			task_list.forEach(task => {
				const { status } = task;
				if (!["Open", "Working", "Overdue", "Pending Review"].includes(status)) {
					frappe.msgprint(`La tarea "${task.name} - ${task.subject}" no puede ser asignada porque su estado es "${__(status)}".`);
					return;
				}
			});

			// tasks can have more than one responsible,
			// so, the user must specify which responsible will be removed
			// and which responsible will be added
			
			const title = __("Asignar Responsable");
			const primary_label = __("Asignar");
			const fields = [
				{
					fieldname: "new_responsible",
					fieldtype: "Link",
					options: "User",
					label: __("Responsable Nuevo"),
					reqd: 1,
				},
			];
			
			function callback({ new_responsible }) {
				frappe.call({
					method: "powerpro.controllers.task.assign_in_bulk",
					args: {
						"task_list": task_list.map(d => d.name),
						"user": new_responsible,
					},
					callback({ message }) {
						frappe.msgprint(message);
						listview.refresh();
					},
				});
			}

			frappe.prompt(fields, callback, title, primary_label);
		}, false);

		listview.page.add_action_item("Re-Assignar", function() {
			// validate the status of all selected tasks
			// all of them must have one of the following statuses:
			// - Open
			// - Working
			// - Overdue
			// - Pending Review ?

			const task_list = listview.get_checked_items();
			task_list.forEach(task => {
				const { status } = task;
				if (!["Open", "Working", "Overdue", "Pending Review"].includes(status)) {
					frappe.msgprint(`La tarea "${task.name} - ${task.subject}" no puede ser re-asignada porque su estado es "${__(status)}".`);
					return;
				}
			});

			// tasks can have more than one responsible,
			// so, the user must specify which responsible will be removed
			// and which responsible will be added
			
			const title = __("Re-Asignar Responsable");
			const primary_label = __("Re-Asignar");
			const fields = [
				{
					fieldname: "prev_responsible",
					fieldtype: "Link",
					options: "User",
					label: __("Responsable Anterior"),
					reqd: 1,
				},
				{
					fieldname: "new_responsible",
					fieldtype: "Link",
					options: "User",
					label: __("Responsable Nuevo"),
					reqd: 1,
				},
			];
			
			function callback({ prev_responsible, new_responsible }) {
				frappe.call({
					method: "powerpro.controllers.task.re_assign_in_bulk",
					args: {
						"task_list": task_list.map(d => d.name),
						"old_user": prev_responsible,
						"new_user": new_responsible,
					},
					callback({ message }) {
						frappe.msgprint(message);
						listview.refresh();
					},
				});
			}

			frappe.prompt(fields, callback, title, primary_label);
		}, false);
	},
};