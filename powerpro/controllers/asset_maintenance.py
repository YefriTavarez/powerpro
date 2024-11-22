# Copyright (c) 2024, Miguel Higuera and contributors
# For license information, please see license.txt


import frappe
from frappe import _, throw
# from frappe.desk.form import assign_to
from . import assign_to
from frappe.model.document import Document
from frappe.desk.form.load import get_assignments
from frappe.utils import add_days, add_months, add_years, getdate, nowdate
from erpnext.assets.doctype.asset_maintenance.asset_maintenance import AssetMaintenance


class AssetMaintenance(AssetMaintenance):
    def on_update(self):
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

    def on_trash(self):
        self.delete_logs_and_todos()

    def delete_logs_and_todos(self):
        doctype = "Asset Maintenance Log"

        for task in self.get("asset_maintenance_tasks"):
            logs = self.get_asset_maintenance_logs(task.name)

            if not logs:
                continue

            for log in logs:
                doc = frappe.get_doc(doctype, log.name)

                if doc.docstatus == 1:
                    doc.cancel()

                doc.delete()


    def get_asset_maintenance_logs(self, task):
        doctype = "Asset Maintenance Log"
        filters = {
            "task": task,
        }
        return frappe.get_all(doctype, filters=filters)


# def assign_tasks(asset_maintenance_name, assign_to_member, maintenance_task, next_due_date, item_code, item_name):
#     team_member = frappe.db.get_value("User", assign_to_member, "email")

#     args = {
#         "doctype": "Asset Maintenance Task",
#         "assign_to": team_member,
#         "name": asset_maintenance_name,
#         "description": maintenance_task,
#         "date": next_due_date,
#         "item_code": item_code,
#         "item_name": item_name,
#         "asset_name": asset_maintenance_name,
#     }

#     existing_todo = frappe.db.get_value(
#         "ToDo",
#         {
#             "reference_type": args["doctype"],
#             "reference_name": args["name"],
#             "description": args["description"],
#             "status": "Open",
#             "allocated_to": ("!=", team_member),
#         },
#         "name",
#     )

#     if existing_todo:
#         frappe.db.set_value("ToDo", existing_todo, "status", "Cancelled")

#     todo_exists = frappe.db.exists(
#         "ToDo",
#         {
#             "reference_type": args["doctype"],
#             "reference_name": args["name"],
#             "description": args["description"],
#             "allocated_to": team_member,
#             "status": "Open",
#         },
#     )

#     if not todo_exists:
#         args["assign_to"] = [args["assign_to"]]
#         assign_to.add(args) 



def update_maintenance_log(asset_maintenance, item_code, item_name, task):
    asset_maintenance_doc = get_asset_maintenance(asset_maintenance)
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
                "maintenance_team": asset_maintenance_doc.maintenance_team,
                "maintenance_manager": asset_maintenance_doc.maintenance_manager,
                "maintenance_manager_name": asset_maintenance_doc.maintenance_manager_name,
            }
        )
        asset_maintenance_log.flags.ignore_permissions = True
        asset_maintenance_log.flags.ignore_validate_update_after_submit = True
        asset_maintenance_log.insert()
    else:
        maintenance_log = frappe.get_doc("Asset Maintenance Log", asset_maintenance_log)
        maintenance_log.assign_to_name = task.assign_to_name
        maintenance_log.task_assignee_email = task.assign_to
        maintenance_log.has_certificate = task.certificate_required
        maintenance_log.description = task.description
        maintenance_log.periodicity = str(task.periodicity)
        maintenance_log.maintenance_type = task.maintenance_type
        maintenance_log.maintenance_team = asset_maintenance_doc.maintenance_team
        maintenance_log.maintenance_manager = asset_maintenance_doc.maintenance_manager
        maintenance_log.maintenance_manager_name = asset_maintenance_doc.maintenance_manager_name

        if not maintenance_log.flags.override_due_date:
            maintenance_log.due_date = task.next_due_date

        maintenance_log.flags.ignore_permissions = True
        maintenance_log.flags.ignore_validate_update_after_submit = True
        maintenance_log.save()


@frappe.whitelist()
def submit_logs(asset_maintenance):
    asset_maintenance_doc = get_asset_maintenance(asset_maintenance)

    for task in asset_maintenance_doc.get("asset_maintenance_tasks"):
        get_planned_maintenance_log(asset_maintenance, task.name, task.next_due_date, asset_maintenance_doc.maintenance_team)


def get_planned_maintenance_log(asset_maintenance, task, due_date, maintenance_team):
    doctype = "Asset Maintenance Log"
    filters = {
        "asset_maintenance": asset_maintenance,
        "task": task,
        "maintenance_status": ("in", ["Planned", "Overdue"]),
        "due_date": due_date,
        "maintenance_team": maintenance_team,
    }

    if name := frappe.db.exists(doctype, filters):
        doc = frappe.get_doc(doctype, name)
        doc.ignore_permissions = True
        doc.submit()


def get_asset_maintenance(asset_maintenance):
    doctype = "Asset Maintenance"
    return frappe.get_doc(doctype, asset_maintenance)


@frappe.whitelist()
def make_dashboard(asset_name, maintenance_team):
	return frappe.db.sql(
		f"""
        Select 
            maintenance_status, 
            count(asset_name) as count, 
            asset_name,
            docstatus
        From 
            `tabAsset Maintenance Log`
        Where 
            asset_name = {asset_name!r} And 
            maintenance_team = {maintenance_team!r}
        Group By 
            maintenance_status,
            docstatus
        """,
		as_dict=1,
	)