# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

from typing import TYPE_CHECKING, Literal, Union
if TYPE_CHECKING:
    from frappe.model import document
    import datetime

# import time
import frappe
from frappe.utils import today, cint

from erpnext.projects.doctype.project import project

class Project(project.Project):
    # override
    def validate(self):  # nosemgrep
        # super(Project, self).validate()

        # if not self.is_new():
        # 	self.copy_from_template()  # nosemgrep
        # self.send_welcome_email()

        self.update_costing()
        self.update_percent_complete()
        self.validate_from_to_dates("expected_start_date", "expected_end_date")
        self.validate_from_to_dates("actual_start_date", "actual_end_date")

        if not frappe.flags.ignore_validate:
            self.render_project_name(for_validate=True)

    def after_insert(self):
        self.copy_from_template()  # nosemgrep

        if self.sales_order:
            frappe.db.set_value("Sales Order", self.sales_order, "project", self.name)


    # override
    def check_for_parent_tasks(self, template_task, project_task, project_tasks):
        if template_task.get("parent_task") \
            and not project_task.get("parent_task"):
            for pt in project_tasks:
                if pt.template_task == template_task.parent_task:
                    project_task.parent_task = pt.name
                    project_task.flags.ignore_links = True
                    project_task.save()
                    break

    # override
    def copy_from_template(self):  # nosemgrep
        """
        Copy tasks from template
        """
        # if self.project_template and not frappe.db.get_all("Task", dict(project=self.name), limit=1):
        if not self.project_template:
            frappe.throw("La Plantilla de Proyecto es obligatoria")
        
    
        # has a template, and no loaded tasks, so lets create
        if not self.expected_start_date:
            # project starts today
            self.expected_start_date = today()

        project_template = frappe.get_doc("Project Template", self.project_template)

        # if not self.project_type: # always override
        self.project_type = project_template.project_type

        # create tasks from project_template
        individual_tasks = []
        task_templates = []
        for task_row in project_template.tasks:
            template_task = frappe.get_doc("Task", task_row.task)
            task_templates.append(template_task)

            # load parent_tasks into task_templates
            task = self.create_task_from_template(template_task, project_template, task_row)
            # db_create_task(task)
            individual_tasks.append(task)

            if template_task.is_group: # type: ignore
                for _template_task in self.load_child_tasks(template_task):
                    task_templates.append(_template_task)
                    task = self.create_task_from_template(_template_task, project_template, task_row)
                    # db_create_task(task)
                    individual_tasks.append(task)

        self.dependency_mapping(task_templates, individual_tasks)
    
    # override
    def dependency_mapping(self, task_templates, individual_tasks):
        for project_task in individual_tasks:
            template_task = frappe.get_doc("Task", project_task.template_task)

            self.check_depends_on_value(template_task, project_task, individual_tasks)
            self.check_for_parent_tasks(template_task, project_task, individual_tasks)

    def check_depends_on_value(self, template_task, project_task, individual_tasks):
        if template_task.get("depends_on") and not project_task.get("depends_on"):
            project_template_map = {pt.template_task: pt for pt in individual_tasks}

            for child_task in template_task.get("depends_on"):
                if project_template_map and project_template_map.get(child_task.task):
                    project_task.reload()  # reload, as it might have been updated in the previous iteration
                    project_task.append(
                        "depends_on", {"task": project_template_map.get(child_task.task).name}
                    ).db_insert()
                    # project_task.save()

    def check_for_parent_tasks(self, template_task, project_task, individual_tasks):
        if template_task.get("parent_task"):
            # if and not project_task.get("parent_task"):
            for pt in individual_tasks:
                if pt.template_task == template_task.parent_task:
                    project_task.parent_task = pt.name
                    project_task.db_update()
                    break


    # override
    def create_task_from_template(
        self, template_task: "document.Document",
        project_template: "document.Document",
        task_row: "document.Document"
    ) -> "document.Document":
        task_expected_start_date, task_expected_end_date = \
            self.get_expected_dates(project_template, task_row)

        task = frappe.get_doc(
            dict(
                doctype="Task",
                subject=template_task.subject,
                project=self.name,
                status="Open",
                exp_start_date=task_expected_start_date,
                exp_end_date=task_expected_end_date,
                expected_time=task_row.get_duration_in_minutes() / 60,
                description=template_task.description,
                task_weight=template_task.task_weight,
                type=template_task.type,
                issue=template_task.issue,
                is_group=template_task.is_group,
                color=template_task.color,
                template_task=template_task.name,
                priority=self.priority,
            )
        )

        existing_users = { d.user for d in task.users }

        for user in self.get_task_users(task_row, template_task):
            if user.user not in existing_users:
                task.append("users", {
                    "user": user.user,
                })

                existing_users.add(user.user)

        task.flags.ignore_mandatory = True
        task.insert()

        return task

    def load_child_tasks(self, template_task: "document.Document") -> list["document.Document"]:
        """
        Load parent tasks into tmp_task_details
        """
        if not template_task.is_group:
            return []

        # if the task is a group, we need to load its child tasks
        child_tasks = frappe.get_all("Task", {
            "parent_task": template_task.name,
            "status": "Template",
        }, pluck="name")

        out = list()
        if child_tasks:
            for child_task in child_tasks:
                child_task_doc = frappe.get_doc("Task", child_task)
                out.append(child_task_doc)

        return out
                
    @frappe.whitelist()
    def render_project_name(self, for_validate=False):
        """
        Render the project name based on the template
        """

        # cache = frappe.cache()
        if self.project_template:
            template = get_project_template(self.project_template)
            project_name = frappe.render_template(
                template.project_name_template, get_context(self)
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

    # override
    def on_trash(self):
        """
        Delete tasks related to this project
        """
        # call on_trash of parent class
        super(Project, self).on_trash()

        # delete tasks related to this project
        frappe.db.delete("Task", dict(project=self.name))


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


    def get_expected_dates(self, project_template, project_template_task):
        gap_in_minutes = cint(project_template.gap_between_tasks) or 30
        expected_start_date = self.expected_start_date

        if not hasattr(self, "last_task_end_date"):
            gap_in_minutes = 0 # first task should start at the project's start date
            self.last_task_end_date = expected_start_date
        
        task_expected_start_date = frappe.utils.add_to_date(
            self.last_task_end_date, minutes=gap_in_minutes
        )

        if department := project_template_task.department:
            _, holiday_list = get_shift_details(department)

            # if shift_type:
            #     start_time, end_time = frappe.get_value(
            #         "Shift Type", shift_type, ["start_time", "end_time"]
            #     )

            #     # # need to validate if the start time of the task is within the shift timings
            #     # # if not, then adjust the start time to the next working day (using holiday list)
            #     # if task_expected_start_date.strftime("%H:%M") < start_time:
            #     #     task_expected_start_date = frappe.utils.add_to_date(
            #     #         task_expected_start_date, days=1
            #     #     )

            # PS: the start and end date fields on the Task are date fields and not datetime fields...
            # so, let's keep it simple for now
            task_expected_start_date = get_working_date_or_next(task_expected_start_date, holiday_list=holiday_list)


        task_expected_end_date = frappe.utils.add_to_date(
            self.last_task_end_date, minutes=project_template_task.get_duration_in_minutes()
        )

        # update last task end date for next task
        self.last_task_end_date = task_expected_end_date

        return task_expected_start_date, task_expected_end_date

    def get_task_users(self, task_row: "document.Document", template_task: "document.Document") -> list["document.Document"]:
        if template_task.users:
            # if the template task has users, we return them
            return [frappe.copy_doc(d) for d in template_task.users]

        assignation_method: Literal[
            "All Employees in the Department",
            "Based on Role",
            "Single User",
        ] = task_row.assignation_method

        if assignation_method == "All Employees in the Department":
            return self._get_users_based_on_department(task_row.department)

        if assignation_method == "Based on Role":
            return self._get_users_based_on_role(
                task_row.role, task_row.department
            )

        if assignation_method == "Single User":
            responsible = frappe.new_doc("Task Responsible")
            responsible.user = task_row.user

            if not responsible.user:
                return []

            return [responsible]

    def _get_users_based_on_department(self, department: str):
        out = list()
        for user in get_users_in_department(department):
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

        all_users_in_department = [
            d.user for d in self._get_users_based_on_department(department)
        ]

        for user in all_users_in_department:
            if user in users_with_role:
                responsible = frappe.new_doc("Task Responsible")
                responsible.user = user

                if responsible.user:
                    out.append(responsible)

        return out


def get_shift_details(department_id):
    doctype = "Department"
    return frappe.get_value(doctype, department_id, ["shift_type", "holiday_list"])


def get_working_date_or_next(date: Union["datetime.date", "datetime.datetime"], holiday_list: str=None) -> "datetime.date":
    while not is_working_date(date, holiday_list=holiday_list):
        date = frappe.utils.add_to_date(date, days=1)
    return date


def is_working_date(date: Union["datetime.date", "datetime.datetime"], holiday_list: str=None) -> bool:
    doctype = "Holiday"
    filters = dict(
        holiday_date=date
    )

    if holiday_list:
        filters["parent"] = holiday_list

    return frappe.db.exists(doctype, filters) is None


def get_project_template(name):
    doctype = "Project Template"
    return frappe.get_doc(doctype, name)


def get_context(doc):
    return frappe._dict(
        frappe=frappe._dict(
            utils=frappe.utils,
            db=frappe.db,
        ),
        doc=doc,
        nowdate=today,
    )


@frappe.whitelist()
def get_users_in_department(department: str) -> list[str]:
    """
    Get all users in a department
    """

    if not department:
        frappe.throw("Department is required")

    if not frappe.db.exists("Department", department):
        frappe.throw(f"Department {department!r} does not exist")

    return [
        d for d in frappe.get_all(
            "Employee",
            filters=dict(
                department=department,
                status="Active"
            ),
            pluck="user_id"
        ) if d
    ]


def db_create_task(task: "document.Document"):
    """
    Create a task in the database
    """
    if task.is_new():
        task.db_insert(ignore_if_duplicate=True)
    else: task.db_update()

    for child in task.get_all_children():
        child.parent = task.name # type: ignore
        if child.is_new():
            child.db_insert(ignore_if_duplicate=True)
        else: child.db_update()
