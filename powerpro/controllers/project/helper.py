# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

from typing import TYPE_CHECKING, Union
if TYPE_CHECKING:
    import datetime


import frappe
from frappe.utils import cint


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
            # if task does not exist in the project, let's ignore it as it might be an optional task
            # optional tasks, when not included in the project will be reported as a broken dependency
            # we will just ignore this, because the user might want to match optional with optional tasks.
            ...
            # frappe.throw(
            #     f"La tarea '{template_name}' no existe en el proyecto '{doc.project}'. "
            #     "Asegurese de NO depender de una tarea que está más abajo en la plantilla. "
            #     "<br>Solo se puede depender de tareas anteriores (ya creadas más arriba en la tabla)."
            # )

    return out


def get_expected_dates(project, project_template, project_template_task):
    gap_in_minutes = cint(project_template.gap_between_tasks) or 30
    expected_start_date = project.expected_start_date

    if not hasattr(project, "last_task_end_date"):
        gap_in_minutes = 0 # first task should start at the project's start date
        project.last_task_end_date = expected_start_date
    
    task_expected_start_date = frappe.utils.add_to_date(
        project.last_task_end_date, minutes=gap_in_minutes
    )

    if department := project_template_task.department:
        _, holiday_list = get_shift_details(department)

        # if shift_type:
        #     start_time, end_time = frappe.get_value(
        #         "Shift Type", shift_type, ["start_time", "end_time"]
        #     )

        #     # # need to validate if the start time of the task is within the shift timings
        #     # # if not, then adjust the start time to the next working day (using holiday list)
        #     # if task_expected_start_date.strftime("%H:%M") < start_time:
        #     #     task_expected_start_date = frappe.utils.add_to_date(
        #     #         task_expected_start_date, days=1
        #     #     )

        # PS: the start and end date fields on the Task are date fields and not datetime fields...
        # so, let's keep it simple for now
        task_expected_start_date = get_working_date_or_next(task_expected_start_date, holiday_list=holiday_list)


    task_expected_end_date = frappe.utils.add_to_date(
        task_expected_start_date, minutes=project_template_task.get_duration_in_minutes()
    )

    # update last task end date for next task
    project.last_task_end_date = task_expected_end_date

    return task_expected_start_date, task_expected_end_date


def get_shift_details(department_id):
    doctype = "Department"
    return frappe.get_value(doctype, department_id, ["shift_type", "holiday_list"])


def get_working_date_or_next(date: Union["datetime.date", "datetime.datetime"], holiday_list: str=None) -> "datetime.date":
    while not is_working_date(date, holiday_list=holiday_list):
        date = frappe.utils.add_to_date(date, days=1)
    return date


def is_working_date(date: Union["datetime.date", "datetime.datetime"], holiday_list: str=None) -> bool:
    doctype = "Holiday"
    filters = dict(
        holiday_date=date
    )

    if holiday_list:
        filters["parent"] = holiday_list

    return frappe.db.exists(doctype, filters) is None


def get_project_template(name):
    doctype = "Project Template"
    return frappe.get_doc(doctype, name)


def get_context(doc):
    return frappe._dict(
        frappe=frappe._dict(
            utils=frappe.utils,
            db=frappe.db,
        ),
        doc=doc,
        nowdate=frappe.utils.today,
    )
