# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


def get_users_from_template(name, as_list=False):
    """
    Retrieve users associated with a Task document used as a project template.
    Args:
        name (str): The name (ID) of the Task document to fetch users from.
        as_list (bool, optional): If True, returns a list of user identifiers (user.user).
            If False, returns a list of copied user documents. Defaults to False.
    Returns:
        list: A list of user identifiers or copied user documents, depending on as_list.
    Raises:
        frappe.exceptions.ValidationError: If the Task document is not a template (status != "Template").
    """

    doctype = "Task"

    doc = frappe.get_doc(doctype, name)

    if not doc.status == "Template":
        frappe.throw("El documento no tiene una plantilla de proyecto asociada.")

    if as_list:
        return [user.user for user in doc.users]
    
    return [
        frappe.copy_doc(user) for user in doc.users
    ]


def get_depends_on_tasks_from_template(project, name, only_names=False):
    """
    Retrieve tasks that the specified task depends on, from a project template.
    Args:
        name (str): The name (ID) of the Task document to fetch dependencies from.
    Returns:
        list: A list of task names that this task depends on.
    Raises:
        frappe.exceptions.ValidationError: If the Task document is not a template (status != "Template").
    """

    doctype = "Task"

    doc = frappe.get_doc(doctype, name)

    if not doc.status == "Template":
        frappe.throw("El documento no tiene una plantilla de proyecto asociada.")

    if not doc.depends_on:
        return []

    if only_names:
        return [task.task for task in doc.depends_on]
    
    out = []
    for row in doc.depends_on:
        template_name = row.task # alias correctly

        # do a get_value to get the name of the task (not the template name)
        # in this project... of course.
        filters = {
            "project": project,
            "template_task": template_name,
        }

        task_name = frappe.get_value(doctype, filters, "name")
        if task_name:
            row = frappe.new_doc("Task Depends On")
            row.task = task_name
            row.idx = row.idx
            row.parent = None  # this will be set later
            row.parenttype = doctype
            row.parentfield = "depends_on"
            out.append(row)
        else:
            frappe.throw(
                f"La tarea '{template_name}' no existe en el proyecto '{doc.project}'. "
                "Asegurese de NO depender de una tarea que está más abajo en la plantilla. "
                "<br>Solo se puede depender de tareas anteriores (ya creadas más arriba en la tabla)."
            )

    return out
