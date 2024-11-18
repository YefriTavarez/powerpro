import frappe

from frappe.desk.form import assign_to
from erpnext.assets.doctype.asset_maintenance_log.asset_maintenance_log import AssetMaintenanceLog
from erpnext.assets.doctype.asset_maintenance.asset_maintenance import calculate_next_due_date


class AssetMaintenanceLog(AssetMaintenanceLog):
    def on_submit(self):
        if self.maintenance_status not in ["Completed", "Cancelled"]:
            frappe.throw(_("Maintenance Status has to be Cancelled or Completed to Submit"))
        self.flags.ignore_permissions = True
        self.update_maintenance_task()

        args = {
            "doctype": "Asset Maintenance Task",
            "assign_to": self.task_assignee_email,
            "name": self.task,
            "description": self.task_name,
            "date": self.due_date,
            "item_code": self.item_code,
            "item_name": self.item_name,
        }
        args["assign_to"] = [args["assign_to"]]
        assign_to.add(args, ignore_permissions=True)

    def update_maintenance_task(self):
        asset_maintenance_doc = frappe.get_doc("Asset Maintenance Task", self.task)

        if self.maintenance_status == "Completed":
            if asset_maintenance_doc.last_completion_date != self.completion_date:
                next_due_date = calculate_next_due_date(
                    periodicity=self.periodicity, last_completion_date=self.completion_date
                )
                asset_maintenance_doc.last_completion_date = self.completion_date
                asset_maintenance_doc.next_due_date = next_due_date
                asset_maintenance_doc.maintenance_status = "Planned"
                asset_maintenance_doc.flags.ignore_permissions = True
                asset_maintenance_doc.save()
        if self.maintenance_status == "Cancelled":
            asset_maintenance_doc.maintenance_status = "Cancelled"
            asset_maintenance_doc.flags.ignore_permissions = True
            asset_maintenance_doc.save()
        asset_maintenance_doc = frappe.get_doc("Asset Maintenance", self.asset_maintenance)
        asset_maintenance_doc.flags.ignore_permissions = True
        asset_maintenance_doc.save()
