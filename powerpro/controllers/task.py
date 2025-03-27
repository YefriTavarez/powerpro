# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

from typing import Union
import frappe

from erpnext.projects.doctype.task import task


class Task(task.Task):
    ...


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
            task_report["status"] = "Failed"
            task_report["message"] = f"User {user} is already assigned to the task."
        else:
            # Add the user
            task.append("users", {"user": user})
            task.save()
            task_report["status"] = "Success"
            task_report["message"] = f"Assigned to {user}."

        report.append(task_report)

    # Generate HTML report
    html_report = "<ul>"
    for entry in report:
        html_report += f"<li><strong>Task ID:</strong> {entry['task_id']} - <strong>Status:</strong> {entry['status']} - <strong>Message:</strong> {entry['message']}</li>"
    html_report += "</ul>"

    return html_report


@frappe.whitelist()
def re_assign_in_bulk(task_list: Union[list, str], old_user: str, new_user: str) -> str:
    """
    Re-assign tasks in bulk and generate an HTML report
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

        # need to find the old_user (if exists) and remove it
        old_user_found = False
        for user in task.users:
            if user.user == old_user:
                task.remove(user)
                old_user_found = True
                break

        if old_user_found:
            # Check if the user already exists in the task's users list
            user_exists = any(u.user == user for u in task.users)

            if user_exists:
                task_report["status"] = "Failed"
                task_report["message"] = f"User {new_user} is already assigned to the task."
            else:
                # add the new_user
                task.append("users", {"user": new_user})
                task.save()
                task_report["status"] = "Success"
                task_report["message"] = f"Reassigned from {old_user} to {new_user}."
        else:
            task_report["status"] = "Failed"
            task_report["message"] = f"Old user {old_user} not found in task."

        report.append(task_report)

    # Generate HTML report
    html_report = "<ul>"
    for entry in report:
        html_report += f"<li><strong>Task ID:</strong> {entry['task_id']} - <strong>Status:</strong> {entry['status']} - <strong>Message:</strong> {entry['message']}</li>"
    html_report += "</ul>"

    return html_report


def get_task(name):
    doctype = "Task"
    return frappe.get_doc(doctype, name)
