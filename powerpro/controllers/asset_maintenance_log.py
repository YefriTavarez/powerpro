import frappe

# from frappe.desk.form import assign_to
from . import assign_to
from frappe import _

from frappe.utils import add_days, add_months, add_years, getdate, nowdate

from erpnext.assets.doctype.asset_maintenance_log.asset_maintenance_log import AssetMaintenanceLog
from erpnext.assets.doctype.asset_maintenance.asset_maintenance import calculate_next_due_date


class AssetMaintenanceLog(AssetMaintenanceLog):
    def validate(self):
        pass

    def on_submit(self):
        args = {
            "doctype": "Asset Maintenance Task",
            "assign_to": self.task_assignee_email,
            "assigne_name": self.assign_to_name,
            "name": self.task,
            "description": self.task_name,
            "date": self.due_date,
            "item_code": self.item_code,
            "item_name": self.item_name,
            "asset_name": self.asset_name,
            "maintenance_team": self.get_maintenance_team(self.asset_maintenance),
            "periodicity": self.periodicity,
            "asset_maintenance_log": self.name,
        }
        args["assign_to"] = [args["assign_to"]]
        assign_to.add(args, ignore_permissions=True)

    def on_trash(self):
        self.delete_todos()

    def update_todo(self):
        if not self.task:
            return

        todo = self.get_todo(self.name)

        if not todo:
            return

        if todo.allocated_to != self.task_assignee_email:
            todo.update({
                "allocated_to": self.task_assignee_email,
                "assigne_name": self.assign_to_name,
            })
            todo.flags.ignore_permissions = True
            todo.save()


    def get_todo(self, log):
        doctype = "ToDo"
        filters = {
            "asset_maintenance_log": log,
        }

        if name := frappe.db.exists(doctype, filters):
            return frappe.get_doc(doctype, name)


    def update_maintenance_task(self):

        # if asset_maintenance_doc.last_completion_date != self.completion_date:
        # next_due_date = calculate_next_due_date(
        #     periodicity=self.periodicity,
        #     start_date=self.due_date,
        # )
        #     asset_maintenance_doc.last_completion_date = self.completion_date
        #     asset_maintenance_doc.next_due_date = next_due_date
        #     asset_maintenance_doc.maintenance_status = "Planned"
        #     asset_maintenance_doc.flags.ignore_permissions = True
        #     asset_maintenance_doc.save()
        if self.maintenance_status == "Cancelled":
            asset_maintenance_doc = frappe.get_doc("Asset Maintenance Task", self.task)
            asset_maintenance_doc.maintenance_status = "Cancelled"
            asset_maintenance_doc.flags.ignore_permissions = True
            asset_maintenance_doc.save()
        # asset_maintenance_doc = frappe.get_doc("Asset Maintenance", self.asset_maintenance)

        # for task in asset_maintenance_doc.asset_maintenance_tasks:
        #     if task.name == self.task:
        #         task.next_due_date = next_due_date
        #         task.maintenance_status = "Planned"
        # asset_maintenance_doc.flags.ignore_permissions = True
        # asset_maintenance_doc.save()

    def get_maintenance_team(self, asset_maintenance):
        doctype = "Asset Maintenance"
        filters = {
            "name": asset_maintenance,
        }
        fields = ["maintenance_team"]

        return frappe.get_value(doctype, filters=filters, fieldname=fields)

    def delete_todos(self):
        if not self.task:
            return

        doctype = "ToDo"
        todos = self.get_todos(self.task)

        if not todos:
            return

        for todo in todos:
            doc = frappe.get_doc(doctype, todo.name)
            doc.flags.ignore_permissions = True
            doc.delete()
        
        self.update_asset_maintenance_due_date()

    def update_asset_maintenance_due_date(self):
        doctype = "Asset Maintenance"
        asset_maintenance = frappe.get_doc(doctype, self.asset_maintenance)
        due_date = calculate_next_due_date(
            periodicity=self.periodicity,
            start_date=nowdate(),
        )

        for task in asset_maintenance.asset_maintenance_tasks:
            if task.name == self.task:
                task.update({
                    "next_due_date": due_date,
                    "maintenance_status": "Planned",
                })

        asset_maintenance.flags.ignore_permissions = True
        asset_maintenance.db_update_all()


    def get_todos(self, task):
        doctype = "ToDo"
        filters = {
            "reference_type": "Asset Maintenance Task",
            "reference_name": task,
        }

        return frappe.get_all(doctype, filters=filters)


def on_update_after_submit(doc, method):
    doc.update_todo()
    doc.update_maintenance_task()
