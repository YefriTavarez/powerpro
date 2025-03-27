# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from frappe.model import document

import frappe
from frappe.utils import today, cint

from erpnext.projects.doctype.project import project

class Project(project.Project):
    # override
    def copy_from_template(self):  # nosemgrep
        """
        Copy tasks from template
        """
        if self.project_template and not frappe.db.get_all("Task", dict(project=self.name), limit=1):
            # has a template, and no loaded tasks, so lets create
            if not self.expected_start_date:
                # project starts today
                self.expected_start_date = today()

            project_template = frappe.get_doc("Project Template", self.project_template)

            if not self.project_type:
                self.project_type = project_template.project_type

            # create tasks from project_template
            project_tasks = []
            tmp_task_details = []
            for project_template_task in project_template.tasks:
                template_task = frappe.get_doc("Task", project_template_task.task)
                tmp_task_details.append(template_task)
                task = self.create_task_from_template(template_task, project_template, project_template_task)
                project_tasks.append(task)

            self.dependency_mapping(tmp_task_details, project_tasks)

    # override
    def create_task_from_template(
        self, task_details: "document.Document",
        project_template: "document.Document",
        project_template_task: "document.Document"
    ) -> "document.Document":
        task_expected_start_date, task_expected_end_date = \
            self.get_expected_dates(project_template, project_template_task)

        task = frappe.get_doc(
            dict(
                doctype="Task",
                subject=task_details.subject,
                project=self.name,
                users=self.get_task_users(project_template_task),
                status="Open",
                exp_start_date=task_expected_start_date,
                exp_end_date=task_expected_end_date,
                expected_time=project_template_task.get_duration_in_minutes() / 60,
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

    def get_expected_dates(self, project_template, project_template_task):
        gap_in_minutes = cint(project_template.gap_between_tasks) or 30
        expected_start_date = self.expected_start_date

        if not hasattr(self, "last_task_end_date"):
            gap_in_minutes = 0 # first task should start at the project's start date
            self.last_task_end_date = expected_start_date
        
        task_expected_start_date = frappe.utils.add_to_date(
            self.last_task_end_date, minutes=gap_in_minutes
        )

        task_expected_end_date = frappe.utils.add_to_date(
            self.last_task_end_date, minutes=project_template_task.get_duration_in_minutes()
        )

        # update last task end date for next task
        self.last_task_end_date = task_expected_end_date

        return task_expected_start_date, task_expected_end_date

    def get_task_users(self, project_template_task: "document.Document"):
        assignation_method: Literal[
            "All Employees in the Department",
            "Based on Role",
            "Single User",
        ] = project_template_task.assignation_method

        if assignation_method == "All Employees in the Department":
            return self._get_users_based_on_department(project_template_task.department)

        if assignation_method == "Based on Role":
            return self._get_users_based_on_role(
                project_template_task.role, project_template_task.department
            )

        if assignation_method == "Single User":
            responsible = frappe.new_doc("Task Responsible")
            responsible.user = project_template_task.user

            if not responsible.user:
                return []

            return [responsible]
    

    def _get_users_based_on_department(self, department: str):
        users = frappe.get_all(
            "Employee",
            filters=dict(department=department),
            pluck="user_id",
        )

        out = list()
        for user in users:
            responsible = frappe.new_doc("Task Responsible")
            responsible.user = user

            if responsible.user:
                out.append(responsible)

        return out
    
    def _get_users_based_on_role(self, role: str, department: str = None):
        users_with_role = frappe.get_all(
            "Has Role",
            filters=dict(role=role),
            pluck="parent",
        )


        out = list()
        if not department:
            for user in users_with_role:
                responsible = frappe.new_doc("Task Responsible")
                responsible.user = user

                if responsible.user:
                    out.append(responsible)
            return out

        all_users_in_department = self._get_users_based_on_department(department)

        for user in all_users_in_department:
            if user in users_with_role:
                responsible = frappe.new_doc("Task Responsible")
                responsible.user = user

                if responsible.user:
                    out.append(responsible)

        return out