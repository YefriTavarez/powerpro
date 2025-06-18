# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from powerpro.controllers.project import helper
from powerpro.controllers.project.utils import get_duration_in_minutes


class Project(Document):
    def after_insert(self):
        self.create_tasks_from_template()

    def validate(self):
        self.validate_required_fields()

    def on_trash(self):
        """
        When a project is deleted, also delete all tasks associated with it.
        """
        tasks = frappe.get_all(
            "Task",
            filters={"project": self.name},
            fields=["name"]
        )

        for task in tasks:
            frappe.delete_doc("Task", task.name, ignore_permissions=True)

    def validate_required_fields(self):
        if not self.project_template:
            frappe.throw("Debes seleccionar una plantilla de proyecto.")

    def create_tasks_from_template(self):
        # template_tasks = frappe.get_all(
        #     "Task",
        #     filters={
        #         "project_template": self.project_template,
        #         "status": "Template",
        #     },
        #     fields=["*"],
        #     order_by="idx asc"
        # )

        def update_task(new_task, template_task):
            new_task.update({
                "project": self.name,
                "subject": template_task.subject,
                "description": template_task.description,
                "is_group": template_task.is_group,
                "task_weight": template_task.task_weight,
                "priority": template_task.priority,
                "issue": template_task.issue,
                "color": template_task.color,
                "type": template_task.type,
                "exp_start_date": None,
                "expected_time": get_duration_in_minutes(duration=.5, measurement="in Days") / 60,
                "exp_end_date": None,
                "status": "Open",
                "parent_task": None,
                "template_task": template_task.name,
                "users": helper.get_users_from_template(template_task.name),
                "depends_on": helper.get_depends_on_tasks_from_template(project=self.name, name=template_task.name),
            })

        template_tasks = frappe.db.sql(
            """
                Select
                    task.color,
                    task.description,
                    task.is_group,
                    task.issue,
                    task.name,
                    task.priority,
                    task.subject,
                    task.task_weight,
                    task.type
                From
                    `tabTask` As task
                Inner Join
                    `tabProject Template Task` As template_task
                On template_task.parent = {project_template!r}
                    And template_task.parenttype = "Project Template"
                    And template_task.parentfield = "tasks"
                Where
                    task.name = template_task.task
                    And task.status = "Template"
                Order By
                    template_task.idx Asc
            """.format(
                project_template=self.project_template
            ),
            as_dict=True
        )

        # Primera pasada: crear tareas sin dependencias
        for template_task in template_tasks:
            if template_task.is_group and frappe.get_all("Task Depends On", filters={"parent": template_task.name}):
                frappe.throw(f"La tarea '{template_task.subject}' es un grupo y no puede tener dependencias.")

            # task_expected_start_date, task_expected_end_date = \
            #     self.get_expected_dates(project_template, task_row)

            new_task = frappe.new_doc("Task")
            
            update_task(new_task, template_task)
            new_task.insert(ignore_permissions=True)

            if template_task.is_group:
                # this is the best moment to create the children tasks,
                # this way they use the correct sequence.
                for child_template_task in frappe.get_all(
                    "Task",
                    filters={
                        "parent_task": template_task.name,
                        "status": "Template"
                    },
                    fields=[
                        "color",
                        "description",
                        "is_group",
                        "issue",
                        "name",
                        "priority",
                        "subject",
                        "task_weight",
                        "type",
                    ]
                ):
                    child_task = frappe.new_doc("Task")
                    update_task(child_task, child_template_task)

                    child_task.parent_task = new_task.name
                    child_task.insert(ignore_permissions=True)

    @frappe.whitelist()
    def get_related_tasks(self):
        """
        Get tasks related to this project
        """
        return frappe.db.sql(
            f"""
            Select
                task.name,
                task.subject,
                task.status,
                Group_Concat(user.full_name SEPARATOR "<br>") As users
            From
                `tabTask` As task
            Left Join
                `tabTask Responsible` As responsible
                On responsible.parent = task.name
                    And responsible.parenttype = "Task"
                    And responsible.parentfield = "users"
                    And IfNull(responsible.user, "") != ""
            Left Join
                `tabUser` As user
                On user.name = responsible.user
            Where
                task.project = {self.name!r}
            Group By
                task.name
            """, as_dict=True
        )
