import frappe


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
    todo.save()

    maintenance_log = get_asset_maintenance_log(task, due_date)
    maintenance_log.update({
        "completion_date": frappe.utils.nowdate(),
        "actions_performed": todo.actions_performed,
        "maintenance_status": "Completed",
    })
    maintenance_log.submit()

    asset_maintenance = get_asset_mainenance(maintenance_log.asset_maintenance)
    # frappe.throw(asset_maintenance.name)

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


def get_asset_mainenance(asset_maintenance):
    doctype = "Asset Maintenance"
    return frappe.get_doc(doctype, asset_maintenance)