# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt


import frappe


__all__ = (
    "reopen_task",
    "complete_task",
    "change_status",
    "request_revision",
)


def reopen_task(hub, task_id):
    """Reopen a task in the Task Hub."""
    task = get_task(task_id)

    # validate the task is not already open
    if task.status != "Completed":
        frappe.throw(f"La tarea {task_id} ya está abierta.")

    task.status = "Open"

    try:
        task.save()
    except frappe.exceptions.ValidationError as e:
        frappe.db.rollback()  # Rollback the transaction
        frappe.log_error()
        frappe.db.commit()  # Commit the Error Log
        return {"status": "error", "message": f"Error al guardar la tarea: {e}"}
    else:
        return {
            "status": "success",
            "message": f"La tarea {task_id} ha sido reabierta.",
        }


def complete_task(hub, task_id):
    """Complete a task in the Task Hub."""
    task = get_task(task_id)

    # validate the task is not already completed
    if task.status == "Completed":
        frappe.throw(f"La tarea {task_id} ya está completada.")

    task.status = "Completed"
    task.completed_on = frappe.utils.today()
    task.completed_by = frappe.session.user

    try:
        task.save()
    except frappe.exceptions.ValidationError as e:
        frappe.db.rollback()  # Rollback the transaction
        frappe.log_error()
        frappe.db.commit()  # Commit the Error Log
        return {"status": "error", "message": f"Error al guardar la tarea: {e}"}
    else:
        return {
            "status": "success",
            "message": f"La tarea {task_id} ha sido completada.",
        }


def change_status(hub, task_id, status):
    """Change the status of a task in the Task Hub."""

    # validate the status is valid:
    # - Open
    # - Working
    # - Pending Review
    # - Overdue
    # - Completed
    # - Cancelled
    valid_statuses = {
        "Open",
        "Working",
        "Pending Review",
        "Overdue",
        "Completed",
        "Cancelled",
    }
    if status not in valid_statuses:
        frappe.throw(f"El estado {_(status)!r} no es válido.")

    task = get_task(task_id)

    # validate the task is not already in the requested status
    if task.status == status:
        frappe.throw(f"La tarea {task_id} ya está en el estado {_(status)!r}.")

    task.status = status

    if status == "Completed":
        task.completed_on = frappe.utils.today()
        task.completed_by = frappe.session.user

    try:
        task.save()
    except frappe.exceptions.ValidationError as e:
        frappe.db.rollback()  # Rollback the transaction
        frappe.log_error()
        frappe.db.commit()  # Commit the Error Log
        return {"status": "error", "message": f"Error al guardar la tarea: {e}"}
    else:
        return {
            "status": "success",
            "message": f"La tarea {task_id} ha sido actualizada a {_(status)!r}.",
        }


def request_revision(hub, task_id):
    """Request a revision for a task in the Task Hub."""

    task = get_task(task_id)

    # validate the task is not already in the requested status
    if task.status == "Pending Review":
        frappe.throw(f"La tarea {task_id} ya está en el estado {_(task.status)!r}.")

    task.status = "Pending Review"

    try:
        task.save()
    except frappe.exceptions.ValidationError as e:
        frappe.db.rollback()  # Rollback the transaction
        frappe.log_error()
        frappe.db.commit()  # Commit the Error Log
        return {"status": "error", "message": f"Error al guardar la tarea: {e}"}
    else:
        return {
            "status": "success",
            "message": f"La tarea {task_id} ha sido actualizada a {_(task.status)!r}.",
        }


def get_task(name):
    doctype = "Task"
    return frappe.get_doc(doctype, name)


def _(text):
	"""Translate text to the current language."""
	if not text:
		return text

	if not isinstance(text, str):
		return text

	if frappe.local.lang in {"es", "es-DO"}:
		# Spanish translations
		try:
			return {
				"Open": "Abierto",
				"Working": "Trabajando",
				"Pending Review": "Pendiente de Revisión",
				"Overdue": "Vencido",
				"Completed": "Completado",
				"Cancelled": "Cancelado",
			}[text]
		except KeyError:
			...

	return frappe._(text)
