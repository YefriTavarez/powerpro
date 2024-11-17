# Copyright (c) 2024, Miguel Higuera and contributors
# For license information, please see license.txt


import frappe
from frappe import _, throw
from frappe.desk.form import assign_to
from frappe.model.document import Document
from frappe.desk.form.load import get_assignments
from frappe.utils import add_days, add_months, add_years, getdate, nowdate
from erpnext.assets.doctype.asset_maintenance.asset_maintenance import AssetMaintenance, update_maintenance_log


class AssetMaintenance(AssetMaintenance):
    def on_update(self):
        for task in self.get("asset_maintenance_tasks"):
            assign_tasks(task.name, task.assign_to, task.maintenance_task, task.next_due_date)
        self.sync_maintenance_tasks()

    def sync_maintenance_tasks(self):
        tasks_names = []
        for task in self.get("asset_maintenance_tasks"):
            tasks_names.append(task.name)
            update_maintenance_log(
                asset_maintenance=self.name, item_code=self.item_code, item_name=self.item_name, task=task
            )
        asset_maintenance_logs = frappe.get_all(
            "Asset Maintenance Log",
            fields=["name"],
            filters={"asset_maintenance": self.name, "task": ("not in", tasks_names)},
        )
        if asset_maintenance_logs:
            for asset_maintenance_log in asset_maintenance_logs:
                maintenance_log = frappe.get_doc("Asset Maintenance Log", asset_maintenance_log.name)
                maintenance_log.db_set("maintenance_status", "Cancelled")


def assign_tasks(asset_maintenance_name, assign_to_member, maintenance_task, next_due_date):
    team_member = frappe.db.get_value("User", assign_to_member, "email")

    args = {
        "doctype": "Asset Maintenance Task",
        "assign_to": team_member,
        "name": asset_maintenance_name,
        "description": maintenance_task,
        "date": next_due_date,
    }

    # Busca un ToDo abierto para la misma tarea (por description) asignado a otro usuario
    existing_todo = frappe.db.get_value(
        "ToDo",
        {
            "reference_type": args["doctype"],
            "reference_name": args["name"],
            "description": args["description"],
            "status": "Open",
            "allocated_to": ("!=", team_member),
        },
        "name",  # Devuelve el nombre del ToDo
    )

    # Cancela el ToDo existente si está asignado a otro usuario
    if existing_todo:
        frappe.db.set_value("ToDo", existing_todo, "status", "Cancelled")

    # Verifica si ya existe un ToDo abierto para este usuario con esta descripción
    todo_exists = frappe.db.exists(
        "ToDo",
        {
            "reference_type": args["doctype"],
            "reference_name": args["name"],
            "description": args["description"],
            "allocated_to": team_member,
            "status": "Open",
        },
    )

    # Si no existe, crea uno nuevo
    if not todo_exists:
        args["assign_to"] = [args["assign_to"]]  # assign_to.add requiere una lista
        assign_to.add(args) 


def update_maintenance_log(asset_maintenance, item_code, item_name, task):
    asset_maintenance_log = frappe.get_value(
        "Asset Maintenance Log",
        {
            "asset_maintenance": asset_maintenance,
            "task": task.name,
            "maintenance_status": ("in", ["Planned", "Overdue"]),
        },
    )

    if not asset_maintenance_log:
        asset_maintenance_log = frappe.get_doc(
            {
                "doctype": "Asset Maintenance Log",
                "asset_maintenance": asset_maintenance,
                "asset_name": asset_maintenance,
                "item_code": item_code,
                "item_name": item_name,
                "task": task.name,
                "has_certificate": task.certificate_required,
                "description": task.description,
                "assign_to_name": task.assign_to_name,
                "task_assignee_email": task.assign_to,
                "periodicity": str(task.periodicity),
                "maintenance_type": task.maintenance_type,
                "due_date": task.next_due_date,
            }
        )
        asset_maintenance_log.insert()
    else:
        maintenance_log = frappe.get_doc("Asset Maintenance Log", asset_maintenance_log)
        maintenance_log.assign_to_name = task.assign_to_name
        maintenance_log.task_assignee_email = task.assign_to
        maintenance_log.has_certificate = task.certificate_required
        maintenance_log.description = task.description
        maintenance_log.periodicity = str(task.periodicity)
        maintenance_log.maintenance_type = task.maintenance_type
        maintenance_log.due_date = task.next_due_date
        maintenance_log.save()
