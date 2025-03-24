# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


from erpnext.projects.doctype.task import task


class Task(task.Task):
    def validate(self):
        super().validate()

        self.check_responsable_is_set()
    
    def check_responsable_is_set(self):
        if self.is_template:
            return

        if not self.responsable:
            frappe.throw("Responsable is required")
