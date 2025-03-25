# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt


from typing import Literal
import frappe

from erpnext.projects.doctype.project_template_task import project_template_task


class ProjectTemplateTask(project_template_task.ProjectTemplateTask):
    def get_duration_in_minutes(self):
        if not self.duration:
            self.duration = 30 # default duration
            self.measurement = "in Minutes"

        if self.measurement == "in Minutes":
            return self.duration
        if self.measurement == "in Hours":
            return self.duration * 60
        if self.measurement == "in Days":
            return self.duration * 60 * 24

    # ERPNext
    task: str 
    subject: str

    # PowerPRO
    duration: int
    measurement: Literal["in Minutes", "in Hours", "in Days"]
    department: str
    assignation_method: Literal["All Employees in the Department", "Based on Role", "Single User"]
    role: str
    user: str
