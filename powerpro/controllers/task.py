# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

from typing import Union
import frappe
from frappe import _

from erpnext.projects.doctype.task import task


class Task(task.Task):
    def autoname(self):
        from frappe.model import naming

        naming_serie = f"{self.project}-.####"
        self.name = naming.make_autoname(naming_serie, doc=self)

    # override
    def on_update(self):
        super().on_update()

        if self.parent_task and not self.flags.from_project:
            self.update_parent_task()

    # override
    def check_recursion(self):
        ...
    # override
    def populate_depends_on(self):
        return # No need to populate depends_on for this custom Task
        if self.parent_task: # if it's child from a group task
            # load the parent task
            parent = frappe.get_doc("Task", self.parent_task)
            if self.name not in [row.task for row in parent.depends_on]:
                parent.append(
                    "depends_on", {"doctype": "Task Depends On", "task": self.name, "subject": self.subject}
                ).db_insert()
                # parent.flags.ignore_links = True
                # parent.flags.from_project = True  # to avoid recursion
                # parent.save()

    # override
    def validate_depends_on_tasks(self):
        if self.depends_on and not self.is_group:
            for task in self.depends_on:
                if not frappe.db.get_value("Task", task.task, "is_template"):
                    dependent_task_format = f"""<a href="/app/task/{task.task}">{task.task}</a>"""
                    frappe.throw(_("Dependent Task {0} is not a Template Task").format(dependent_task_format))


    def update_parent_task(self):
        """Update the parent task's status based on the current task's status and the other children."""
        parent_task = frappe.get_doc("Task", self.parent_task)

        # Get all child tasks
        child_tasks = frappe.get_all(
            "Task", filters={"parent_task": self.parent_task}, fields=["name", "status"]
        )

        determined_new_status = parent_task.status  # Initialize with current status

        if not child_tasks:  # No child tasks
            # If there are no children, the parent task might be considered 'Open' or 'Working'
            # unless explicitly set otherwise. Or, if it has no children and isn't a group task,
            # its status is independent. For now, let's assume it becomes "Completed" if it has no children.
            # This behavior might need refinement based on specific business logic.
            determined_new_status = "Completed"
        else:
            statuses = [
                task["status"] for task in child_tasks
            ]  # Corrected access to status
            num_total_children = len(statuses)
            num_completed = statuses.count("Completed")
            num_cancelled = statuses.count("Cancelled")

            if num_completed == num_total_children:  # All children are completed
                determined_new_status = "Completed"
            # If any child is Cancelled, and not all are completed, the logic from comments was:
            # "if more are cancelled than completed, then cancelled"
            # "else completed" (This "else completed" seems problematic if some are open/working)
            # Let's refine this:
            # 1. If all are completed -> Parent Completed
            # 2. If all are cancelled -> Parent Cancelled
            # 3. If a mix including cancelled:
            #    - If cancelled outnumber completed (and not all are completed) -> Parent Cancelled
            #    - Otherwise (e.g., mix of open, working, completed, some cancelled but not majority)
            #      the parent might be "Working" or "Open". The original comment said "else completed",
            #      which might be an oversimplification.
            # For now, sticking to the provided comment's logic as closely as possible:
            # "completed if all children are completed or any cancelled" - this part is tricky.
            # "if more are cancelled than completed, then cancelled"
            # "else completed"

            # Re-interpreting the comments:
            # Priority 1: All children completed -> Parent Completed
            if all(status == "Completed" for status in statuses):
                determined_new_status = "Completed"
            # Priority 2: All children open -> Parent Open
            elif all(status == "Open" for status in statuses):
                determined_new_status = "Open"  # If all are Open, set parent to Open
            # Priority 3: If any child is Cancelled, and not all are Completed.
            elif any(status == "Cancelled" for status in statuses):
                # "if more are cancelled than completed, then cancelled"
                if num_cancelled > num_completed:
                    determined_new_status = "Cancelled"
                # The original comment "any cancelled ... else completed"
                # This implies if there's any cancellation and it doesn't meet "more cancelled than completed",
                # it defaults to "Completed". This seems like a specific business rule.
                else:  # This branch covers "any cancelled" and (num_cancelled <= num_completed)
                    # and not all are completed.
                    determined_new_status = "Completed"
            # Priority 3: No cancellations, not all completed, implies some are Open/Working.
            # The original comments didn't explicitly cover this, defaulting to "Completed"
            # if the "any cancelled" condition wasn't met after the "all completed" check.
            # If we strictly follow "else completed" from the original logic block:
            elif not all(status == "Completed" for status in statuses) and not any(
                status == "Cancelled" for status in statuses
            ):
                # This means all tasks are in states like Open, Working, Overdue etc.
                # The original logic would have led to "Completed" here if we follow the last "else".
                # This seems unlikely. A more logical state would be "Working" or "Open".
                # However, to adhere to the "else completed" implication from the original comments' structure:
                # If we assume the original logic was:
                # 1. all completed -> completed
                # 2. (else if) any cancelled AND any completed: -> cancelled (this was the original code)
                #    My interpretation of comments: "if more are cancelled than completed, then cancelled else completed"
                # The original code had:
                # elif any(status == "Cancelled" for status in statuses) \
                #    and any(status == "Completed" for status in statuses):
                #    parent_task.status = "Cancelled"
                # This is different from "more cancelled than completed".
                # Let's stick to the new interpretation of the comments.
                # If after all checks, no specific rule applied, and not all are completed,
                # and no cancellations, it implies tasks are ongoing.
                # The original comment "else completed" is the final fallback.
                pass  # Keep determined_new_status as is, or set to "Working" if that's more logical.
                # For now, if it falls through, it means not all completed, no cancellations dominant.
                # The original logic's final "else completed" is what we're trying to implement.
                # If not all completed, and not (any cancelled and more cancelled > completed),
                # then it should be "Completed" by the original comment's final "else".
                if (
                    determined_new_status != "Completed"
                    and determined_new_status != "Cancelled"
                ):  # if not already set by a rule
                    # This case means not all are completed, and the cancellation rules didn't make it Cancelled.
                    # The final "else completed" from the comments.
                    is_any_open_working = any(
                        s not in ["Completed", "Cancelled"] for s in statuses
                    )
                    if is_any_open_working:
                        # If there are open/working tasks and no dominant cancellation,
                        # parent should likely be 'Working' or 'Open'.
                        # Let's assume 'Working' if not all are done and no cancellation takes precedence.
                        determined_new_status = (
                            "Working"  # A more sensible default than "Completed"
                        )
                    else:
                        # This case implies all are either Completed or Cancelled, but not all are Completed,
                        # and the "more cancelled than completed" rule didn't fire.
                        # e.g. 2 completed, 2 cancelled.
                        # The original comment "else completed" would apply.
                        determined_new_status = "Completed"

        # Update and save only if the status has changed
        if parent_task.status != determined_new_status:
            parent_task.status = determined_new_status


            parent_task.save()


@frappe.whitelist()
def assign_in_bulk(task_list: Union[list, str], user: str) -> str:
    """
    Assign tasks in bulk
    """

    if isinstance(task_list, str):
        if "[" in task_list:
            task_list = eval(task_list)
        else:
            task_list = [task_list]

    report = []

    for task_id in task_list:
        task = get_task(task_id)
        task_report = {"task_id": task_id, "status": "", "message": ""}

        # Check if the user already exists in the task's users list
        user_exists = any(u.user == user for u in task.users)

        if user_exists:
            task_report["status"] = "Fallido"
            task_report["message"] = f"El Usuario {user!r} ya está asignado a la Tarea."
        else:
            # Add the user
            task.append("users", {"user": user})
            task.save()
            task_report["status"] = "Éxito"
            task_report["message"] = f"Asignado a {user!r}."

        report.append(task_report)

    # Generate HTML report
    html_report = "<ul>"
    for entry in report:
        html_report += f"""
            <li>
                <p>
                    <strong>ID de Tarea:</strong> {entry['task_id']} 
                    <br>
                    <strong>Estado:</strong> {entry['status']}
                    <br>
                    <strong>Mensaje:</strong> {entry['message']}
                </p>
            </li>
        """

    html_report += "</ul>"

    return html_report


@frappe.whitelist()
def re_assign_in_bulk(task_list: Union[list, str], old_user: str, new_user: str) -> str:
    """
    Re-assign tasks in bulk and generate an HTML report
    """

    # validate old_user != new_user
    if old_user == new_user:
        return frappe.throw("No se pueden re-asignar Tareas al mismo Usuario.")

    if isinstance(task_list, str):
        if "[" in task_list:
            task_list = eval(task_list)
        else:
            task_list = [task_list]

    report = []

    for task_id in task_list:
        task = get_task(task_id)
        task_report = {"task_id": task_id, "status": "", "message": ""}

        # need to find the old_user (if exists) and remove it
        old_user_found = False
        for user in task.users:
            if user.user == old_user:
                task.remove(user)
                old_user_found = True
                break

        if old_user_found:
            # Check if the user already exists in the task's users list
            user_exists = any(u.user == new_user for u in task.users)

            if user_exists:
                task_report["status"] = "Fallido"
                task_report["message"] = (
                    f"El Usuario {new_user!r} ya está asignado a la Tarea."
                )
            else:
                # add the new_user
                task.append("users", {"user": new_user})
                task.save()
                task_report["status"] = "Éxito"
                task_report["message"] = f"Re-asignado de {old_user!r} a {new_user!r}."
        else:
            task_report["status"] = "Fallido"
            task_report["message"] = (
                f"No se encontró al usuario anterior {old_user!r} en la tarea."
            )

        report.append(task_report)

    # Generate HTML report
    html_report = "<ul>"
    for entry in report:
        html_report += f"""
            <li>
                <p>
                    <strong>ID de Tarea:</strong> {entry['task_id']}
                    <br>
                    <strong>Estado:</strong> {entry['status']}
                    <br>
                    <strong>Mensaje:</strong> {entry['message']}
                </p>
            </li>
        """
    html_report += "</ul>"

    return html_report


def get_task(name):
    doctype = "Task"
    return frappe.get_doc(doctype, name)
