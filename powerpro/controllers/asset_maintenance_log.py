import frappe

from frappe.desk.form import assign_to
from erpnext.assets.doctype.asset_maintenance_log.asset_maintenance_log import AssetMaintenanceLog


class AssetMaintenanceLog(AssetMaintenanceLog):
    def on_submit(self):
        if self.maintenance_status not in ["Completed", "Cancelled"]:
            frappe.throw(_("Maintenance Status has to be Cancelled or Completed to Submit"))
        self.update_maintenance_task()

        args = {
            "doctype": "Asset Maintenance Task",
            "assign_to": self.task_assignee_email,
            "name": self.task,
            "description": self.task_name,
            "date": self.due_date,
        }
        args["assign_to"] = [args["assign_to"]]
        assign_to.add(args)
