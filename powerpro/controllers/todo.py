import frappe
from erpnext.assets.doctype.asset_maintenance.asset_maintenance import calculate_next_due_date


@frappe.whitelist()
def close_maintenance_task(todo, task, due_date):
    todo = get_todo(todo)

    if not todo.actions_performed:
        frappe.throw(
            "Debe especificar las acciones realizadas durante esta tarea para poder cerrar el mantenimiento."
        )
    todo.update({
        "status": "Closed",
    })
    todo.flags.ignore_permissions = True
    todo.save()

    maintenance_log = get_asset_maintenance_log(task, due_date)
    maintenance_log.update({
        "completion_date": frappe.utils.nowdate(),
        "actions_performed": todo.actions_performed,
        "completed_by": frappe.session.user,
        "completed_by_name": frappe.get_value("User", frappe.session.user, "full_name"),
        "maintenance_status": "Completed",
    })
    maintenance_log.flags.ignore_permissions = True
    maintenance_log.flags.ignore_validate_update_after_submit = True
    maintenance_log.save()

    if not todo.is_old_maintenance:
        create_next_maintenance_log(maintenance_log)


def create_next_maintenance_log(log):
    asset_maintenance = get_asset_maintenance(log.asset_maintenance)

    due_date = calculate_next_due_date(
        periodicity=log.periodicity,
        start_date=log.due_date,
    )

    asset_maintenance = get_asset_maintenance(log.asset_maintenance)

    for task in asset_maintenance.asset_maintenance_tasks:
        if task.name == log.task:
            task.update({
                "next_due_date": due_date,
                "maintenance_status": "Planned",
            })

    asset_maintenance.flags.ignore_permissions = True
    asset_maintenance.save()


@frappe.whitelist()
def reopen_maintenance_task(todo, task, due_date):
    todo = get_todo(todo)
    todo.update({
        "status": "Open",
        "is_old_maintenance": True,
    })
    todo.flags.ignore_permissions = True
    todo.save()

    log = get_completed_asset_maintenance_log(todo.asset_maintenance_log)
    log.update({
        "completion_date": None,
        "actions_performed": None,
        "maintenance_status": "Planned",
        "completed_by": None,
    })
    log.flags.ignore_permissions = True
    log.db_update()



def get_todo(todo):
    doctype = "ToDo"
    return frappe.get_doc(doctype, todo)


def get_asset_maintenance_log(task, due_date):
    doctype = "Asset Maintenance Log"
    filters = {
        "task": task,
        "due_date": due_date,
        "maintenance_status": ("in", ["Planned", "Overdue"]),
    }
    return frappe.get_doc(doctype, filters)


def get_completed_asset_maintenance_log(log):
    doctype = "Asset Maintenance Log"

    if name := frappe.db.exists(doctype, log):
        return frappe.get_doc(doctype, name)


def get_asset_maintenance(asset_maintenance):
    doctype = "Asset Maintenance"
    return frappe.get_doc(doctype, asset_maintenance)

