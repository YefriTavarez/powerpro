# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from frappe.utils import add_days, date_diff, getdate

from erpnext.projects.doctype.task import task

class Task(Document):
    def validate(self):
        self.validate_dependency_rules()
        self.validate_group_rules()
        self.validate_group_tasks()

        self.erpnext_validate()

    def erpnext_validate(self):
        # task.Task.validate_dates(self)
        task.Task.validate_from_to_dates(self, "exp_start_date", "exp_end_date")
        task.Task.validate_from_to_dates(self, "act_start_date", "act_end_date")
        task.Task.validate_parent_expected_end_date(self)
        task.Task.validate_parent_project_dates(self)

        task.Task.validate_progress(self)
        task.Task.validate_status(self)
        # extend validate_status
        if self.status == "Template" and self.project:
            frappe.throw("No se puede establecer el estado de la tarea como 'Template' si está asociada a un proyecto.")

        task.Task.update_depends_on(self)
        # task.Task.validate_dependencies_for_template_task(self)
        if self.is_template:
            task.Task.validate_parent_template_task(self)
            task.Task.validate_depends_on_tasks(self)

        task.Task.validate_completed_on(self)

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

    def validate_group_tasks(self):
        """Group Tasks cannot be manually closed or completed.
        All sub-tasks must be closed or completed before closing the group task.
        """

        # Task status list:
        #     - Open
        #     - Working
        #     - Pending Review
        #     - Overdue
        #     - Template
        #     - Completed
        #     - Cancelled

        if self.is_group and self.status in ["Completed", "Cancelled"]:
            sub_tasks = frappe.get_all("Task", filters={"parent_task": self.name, "status": ["in", ["Open", "Working", "Pending Review", "Overdue"]]}, fields=["name"])
            if sub_tasks:
                frappe.throw(f"No se puede cerrar o completar la tarea grupo '{self.name}' porque tiene sub-tareas pendientes: {', '.join([task.name for task in sub_tasks])}.")
            