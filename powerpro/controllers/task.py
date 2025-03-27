# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe

from erpnext.projects.doctype.task import task


class Task(task.Task):
    ...


@frappe.whitelist()
def re_assign_in_bulk(task_list: list, old_user: str, new_user: str) -> str:
    """
    Re-assign tasks in bulk
    """
    for task_id in task_list:
        task = get_task(task_id)

        # need to find the old_user (if exists) and remove it
        for user in task.users:
            if user.user == old_user:
                task.remove("users", user)
                break
        
        # add the new_user
        task.append("users", {"user": new_user})
        task.save()


def get_task(name):
    doctype = "Task"
    return frappe.get_doc(doctype, name)
