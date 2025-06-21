# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from frappe.utils import add_days, date_diff, getdate

class Task(Document):
    def validate(self):
        self.validate_dependency_rules()
        self.validate_group_rules()

    def on_update(self):
        # self.update_nsm_model()
        self.reschedule_dependent_tasks()
        self.update_project()

    def reschedule_dependent_tasks(self):
        end_date = self.exp_end_date or self.act_end_date
        if end_date:
            for task_name in frappe.db.sql(
                """
                select name from `tabTask` as parent
                where parent.project = %(project)s
                    and parent.name in (
                        select parent from `tabTask Depends On` as child
                        where child.task = %(task)s and child.project = %(project)s)
            """,
                {"project": self.project, "task": self.name},
                as_dict=1,
            ):
                task = frappe.get_doc("Task", task_name.name)
                if (
                    task.exp_start_date
                    and task.exp_end_date
                    and task.exp_start_date < getdate(end_date)
                    and task.status == "Open"
                ):
                    task_duration = date_diff(task.exp_end_date, task.exp_start_date)
                    task.exp_start_date = add_days(end_date, 1)
                    task.exp_end_date = add_days(task.exp_start_date, task_duration)
                    task.flags.ignore_recursion_check = True
                    task.save()

    def update_project(self):
        if self.project and not self.flags.from_project:
            frappe.get_cached_doc("Project", self.project).update_project()


    def validate_dependency_rules(self):
        for dep in self.depends_on:
            if dep.task == self.name:
                frappe.throw("Una tarea no puede depender de sí misma.")

            if frappe.db.get_value("Task", dep.task, "is_group"):
                frappe.throw(f"No se puede depender de una tarea grupo: {dep.task}")

    def validate_group_rules(self):
        if self.is_group:
            if self.depends_on:
                for dep in self.depends_on:
                    if dep.task == self.name:
                        frappe.throw("Una tarea grupo no puede depender de sí misma.")

                    if frappe.db.get_value("Task", dep.task, "is_group"):
                        frappe.throw(f"No se puede depender de una tarea grupo: {dep.task}")
                    
                    if frappe.db.get_value("Task", dep.task, "parent_task") != self.name:
                        frappe.throw(f"Una tarea grupo no puede depender de una tarea que no sea su sub-tarea: {dep.task}")

            if self.users:
                frappe.throw("Las tareas grupo no deben tener responsables.")
