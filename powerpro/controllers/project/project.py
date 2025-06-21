# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from erpnext.projects.doctype.project import project

from powerpro.controllers.project import helper
from powerpro.controllers.project.utils import get_duration_in_minutes


class Project(Document):
    def onload(self):
        self.set_onload(
            "activity_summary",
            frappe.db.sql(
                """select activity_type,
            sum(hours) as total_hours
            from `tabTimesheet Detail` where project=%s and docstatus < 2 group by activity_type
            order by total_hours desc""",
                self.name,
                as_dict=True,
            ),
        )

    def before_print(self, settings=None):
        self.onload()

    def after_insert(self):
        self.create_tasks_from_template()

    def validate(self):
        self.update_percent_complete()
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

        frappe.db.sql(
            f"""
            Delete
            From
                `tabTask Depends On`
            Where
                task Like "PROY-%"
                And parent in (
                    Select name From `tabTask`
                    Where project = {self.name!r}
                )
            """
        )

        for task in tasks:
            frappe.delete_doc("Task", task.name, ignore_permissions=True)


    def update_project(self):
        """Called externally by Task"""

        # erpnext_project = Project(doctype=self.doctype)
        project.Project.update_percent_complete(self)
        project.Project.update_costing(self)
        self.db_update()

    # overrides of update_costing
    update_purchase_costing = project.Project.update_purchase_costing
    update_sales_amount = project.Project.update_sales_amount
    update_billed_amount = project.Project.update_billed_amount
    calculate_gross_margin = project.Project.calculate_gross_margin
    get_billed_amount_from_parent = project.Project.get_billed_amount_from_parent
    get_billed_amount_from_child = project.Project.get_billed_amount_from_child

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
                "department": template_task.department,
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
                    Coalesce(task.department, template_task.department) As department,
                    task.type,
                    template_task.name As template_task_id
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
            # if template_task.is_group and frappe.get_all("Task Depends On", filters={"parent": template_task.name}):
            #     frappe.throw(f"La tarea '{template_task.subject}' es un grupo y no puede tener dependencias.")

            project_template = helper.get_project_template(self.project_template)
            [task_row] = project_template.get("tasks", {
                "name": template_task.template_task_id,
            })
            task_expected_start_date, task_expected_end_date = \
                helper.get_expected_dates(self, project_template, task_row)

            new_task = frappe.new_doc("Task")
            
            update_task(new_task, template_task)
            new_task.exp_start_date = task_expected_start_date
            new_task.exp_end_date = task_expected_end_date
            new_task.expected_time = get_duration_in_minutes(
                duration=template_task.task_weight or 0,
                measurement=template_task.type or "in Minutes"
            ) / 60
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

                    # Set expected dates and tima same as parent task
                    child_task.exp_start_date = new_task.exp_start_date
                    child_task.exp_end_date = new_task.exp_end_date
                    child_task.expected_time = new_task.expected_time

                    child_task.department = new_task.department
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

    @frappe.whitelist()
    def render_project_name(self, for_validate=False):
        """
        Render the project name based on the template
        """

        # cache = frappe.cache()
        if self.project_template:
            template = helper.get_project_template(self.project_template)
            project_name = frappe.render_template(
                template.project_name_template, helper.get_context(self)
            )

            if self.project_name != project_name:
                self.project_name = project_name

                # if not for_validate:
                #     cache_key = f"project_name_update_{self.name}"
                #     last_msg_time = cache.get(cache_key)
                #     current_time = time.time()

                #     if not last_msg_time or current_time - float(last_msg_time) > 5:  # Throttle to 5 seconds
                #         frappe.msgprint(
                #             "Nombre del Proyecto ha sido actualizado",
                #             alert=True, realtime=True
                #         )
                #         cache.set(cache_key, current_time)
        else:
            if for_validate:
                frappe.throw("La Plantilla de Proyecto es obligatoria")
            return
