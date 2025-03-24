# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt


import frappe
from erpnext.projects.doctype.project import project


class Project(project.Project):
    # override
    def create_task_from_template(self, task_details: dict):
        # super().after_insert()
        task = frappe.get_doc(
            dict(
                doctype="Task",
                subject=task_details.subject,
                project=self.name,
                responsable=self.get_responsable(),
                status="Open",
                exp_start_date=self.calculate_start_date(task_details),
                exp_end_date=self.calculate_end_date(task_details),
                description=task_details.description,
                task_weight=task_details.task_weight,
                type=task_details.type,
                issue=task_details.issue,
                is_group=task_details.is_group,
                color=task_details.color,
                template_task=task_details.name,
                priority=task_details.priority,
            )
        )

        task.flags.ignore_mandatory = True
        task.insert()

        return task

    def get_responsable(self):
        return "Administrator" # ToDo: Implement this method