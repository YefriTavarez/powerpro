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

        if self.is_group and self.parent_task:
            # mutilevel group tasks are not allowed
            frappe.throw("Una tarea grupo no puede tener una tarea padre.")

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


    def watch_status_change(self):
        previous = self.get_doc_before_save()
        
        # Handle status change events
        if previous.status != self.status:
            # Call a generic handler for all status transitions
            self.run_method("on_status_change", previous.status, self.status)
            
            # Call a handler specific to the new status (e.g., on_completed, on_opened, etc.)
            method_name = f"on_{self.status.lower().replace(' ', '_')}"
            self.run_method(method_name)
            
            # Optional: If reopening logic is needed
            if previous.status in ("Completed", "Cancelled") and self.status == "Open":
                self.run_method("on_reopened")

    # on_opened - Status changes to Open from any other
    # Task is newly opened or reset
    
    # on_started - Status changes to Working
    # Actual work begins
    
    # on_pending_review - Status changes to Pending Review
    # Task is ready for feedback
    
    # on_overdue - Status changes to Overdue
    # Deadline missed
    
    # on_completed - Status changes to Completed
    # Work is finalized
    
    # on_cancelled - Status changes to Cancelled
    # Task is aborted

    # on_template_mode - Status changes to Template
    # Task is used as a blueprint
    
    # on_reopened - Status changes from Completed, Cancelled, etc., to Open
    # Resumed task

    # on_status_change - Any change in status
    # Generic handler for logging, notifications, etc.


    def on_update(self):
        # self.update_nsm_model()
        self.reschedule_dependent_tasks()
        self.update_project()
        self.watch_status_change()

    def on_status_change(self, previous_status, new_status):
        """Generic method to handle status changes.
        Can be overridden for custom behavior."""

        if self.parent_task:
            update_parent_status(self.name)

    def on_close(self):
        """method to be executed when the task is closed"""

    def on_reopen(self):
        """method to be executed when the task is closed or reopened"""

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
                as_dict=True,
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


def update_parent_status(task: str):
    if isinstance(task, str):
        task = frappe.get_doc("Task", task)

    parent_name = task.parent_task
    if not parent_name:
        return  # No parent to update

    # Get all children of this parent
    children = frappe.get_all(
        "Task",
        filters={"parent_task": parent_name},
        fields=["name", "status"]
    )

    if not children:
        return  # No children found — shouldn't happen, but safe guard

    status_list = [d.status for d in children if d.status != "Template"]

    if not status_list:
        return  # All children are Templates, no action needed

    # Priority-based resolution
    resolved_status = None

    if all(d == "Completed" for d in status_list):
        resolved_status = "Completed"
    elif any(d == "Overdue" for d in status_list):
        resolved_status = "Overdue"
    elif any(d == "Working" for d in status_list):
        resolved_status = "Working"
    elif any(d == "Pending Review" for d in status_list):
        resolved_status = "Pending Review"
    elif all(d == "Cancelled" for d in status_list):
        resolved_status = "Cancelled"
    elif all(d == "Open" for d in status_list):
        resolved_status = "Open"
    else:
        # Mixed state — fallback to "Open" if not actively working
        resolved_status = "Open"

    # Update parent if changed
    parent_task = frappe.get_doc("Task", parent_name)
    if parent_task.status != resolved_status:
        parent_task.db_set("status", resolved_status)
