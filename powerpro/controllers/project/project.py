# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from erpnext.projects.doctype.project import project

from powerpro.controllers.project import helper
from powerpro.controllers.project.utils import get_duration_in_minutes
from frappe.utils import flt
from erpnext.selling.doctype.sales_order.sales_order import (
    make_delivery_note as so_make_delivery_note,
    make_sales_invoice as so_make_sales_invoice,
)


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
        optional_tasks_included = False
        optional_tasks = []
        if hasattr(self, "_optional_tasks_included"):
            optional_tasks = frappe.parse_json(
                getattr(self, "_optional_tasks", "[]")
            )

            optional_tasks_included = True

        self.create_tasks_from_template(
            optional_tasks, optional_tasks_included
        )

    def validate(self):
        project.Project.update_percent_complete(self)
        self.validate_required_fields()

    def on_trash(self):
        """
        When a project is deleted, also delete all tasks associated with it.
        """

        frappe.db.sql(
            f"""
            Delete
            From
                `tabTask Depends On`
            Where
                parent in (
                    Select name From `tabTask`
                    Where project = {self.name!r}
                )
            """
        )

        frappe.db.sql(
            f"""
            Delete
            From
                `tabTask Responsible`
            Where
                parent in (
                    Select name From `tabTask`
                    Where project = {self.name!r}
                )
            """
        )

        frappe.db.sql(
            f"""
            Delete
            From
                `tabTask`
            Where
                project = {self.name!r}
            """
        )

    def update_project(self):
        """Called externally by Task"""

        # erpnext_project = Project(doctype=self.doctype)
        project.Project.update_percent_complete(self)
        project.Project.update_costing(self)


        self.modified = frappe.utils.now()
        self.modified_by = frappe.session.user
        self.db_update()

        self.notify_update()

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

    def create_tasks_from_template(self, optional_tasks=None, optional_tasks_included=False):
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

        optional_tasks_condition = ""
        if optional_tasks_included:
            if optional_tasks:
                optional_tasks_condition = """
                    And (
                        template_task.is_optional = 0
                        Or (
                            template_task.is_optional = 1
                                And template_task.task In ({})
                        )
                    )
                """.format(
                    ", ".join(frappe.db.escape(task) for task in optional_tasks)
                )
            else:
                optional_tasks_condition = "And template_task.is_optional = 0"
            

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
                    {optional_tasks_condition}
                Order By
                    template_task.idx Asc
            """.format(
                project_template=self.project_template,
                optional_tasks_condition=optional_tasks_condition,
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


@frappe.whitelist()
def make_delivery_note_from_project(project_id: str):
    """Create a Delivery Note from the Sales Order linked to the given Project,
    restricted to a single item and quantity.
    Returns a doc to be opened via open_mapped_doc on the client.
    """
    args = frappe.flags.args

    # project = args.project
    item_code = args.item_code
    qty = args.qty
    sales_order = args.sales_order
    qty = flt(args.qty)

    # qty = flt(qty)
    if qty <= 0:
        frappe.throw(_("Quantity must be greater than zero."))

    if not sales_order:
        sales_order = frappe.db.get_value("Project", project_id, "sales_order")

    if not sales_order:
        frappe.throw(_("Sales Order is required."))


    so = frappe.get_doc("Sales Order", sales_order)
    if so.docstatus != 1:
        frappe.throw(_("Sales Order {0} must be submitted.").format(so.name))

    # Let ERPNext build the remaining-to-deliver DN, then keep only the requested item
    dn = so_make_delivery_note(so.name)

    # Pick the first mapped line for the requested item
    target_row = None
    for row in dn.items:
        if row.item_code == item_code:
            target_row = row
            break

    if not target_row:
        frappe.throw(_("No pending quantity to deliver for item {0} on Sales Order {1}.").format(item_code, so.name))

    max_qty = flt(target_row.qty)
    if qty > max_qty:
        frappe.throw(_("Requested quantity {0} exceeds pending to deliver {1} for item {2}.").format(qty, max_qty, item_code))

    # Keep only this row and set the requested qty
    dn.items = [target_row]
    dn.items[0].qty = qty

    # Ensure SO links present
    if not getattr(dn.items[0], 'against_sales_order', None):
        dn.items[0].against_sales_order = so.name

    dn.run_method("set_missing_values")
    dn.run_method("calculate_taxes_and_totals")
    return dn


@frappe.whitelist()
def make_sales_invoice_from_project(project_id: str):
    """Create a Sales Invoice from the Sales Order linked to the given Project,
    restricted to a single item and quantity (or amount for unit-price rows).
    Returns a doc to be opened via open_mapped_doc on the client.
    """
    args = frappe.flags.args
    # project = args.project
    item_code = args.item_code
    sales_order = args.sales_order
    qty = flt(args.qty)

    # qty = flt(qty)
    if qty <= 0:
        frappe.throw(_("Quantity must be greater than zero."))

    if not sales_order:
        sales_order = frappe.db.get_value("Project", project_id, "sales_order")

    if not sales_order:
        frappe.throw(_("Sales Order is required."))

    so = frappe.get_doc("Sales Order", sales_order)
    if so.docstatus != 1:
        frappe.throw(_("Sales Order {0} must be submitted.").format(so.name))

    # Let ERPNext build the remaining-to-bill SI, then keep only the requested item
    si = so_make_sales_invoice(so.name)

    target_row = None
    for row in si.items:
        if row.item_code == item_code:
            target_row = row
            break

    if not target_row:
        frappe.throw(_("No pending amount/qty to bill for item {0} on Sales Order {1}.").format(item_code, so.name))

    # If the mapped row has a qty > 0, treat input as qty; otherwise treat as amount
    if flt(getattr(target_row, 'qty', 0)) > 0:
        max_qty = flt(target_row.qty)
        if qty > max_qty:
            frappe.throw(_("Requested quantity {0} exceeds pending to bill {1} for item {2}.").format(qty, max_qty, item_code))
        target_row.qty = qty
    else:
        # amount-based (unit price rows)
        max_amt = abs(flt(getattr(target_row, 'amount', 0)))
        if qty > max_amt:
            frappe.throw(_("Requested amount {0} exceeds pending to bill {1} for item {2}.").format(qty, max_amt, item_code))
        target_row.amount = qty
        if flt(getattr(target_row, 'rate', 0)):
            target_row.qty = qty / flt(target_row.rate)

    si.items = [target_row]

    # Ensure SO link present
    if not getattr(si.items[0], 'sales_order', None):
        si.items[0].sales_order = so.name

    si.run_method("set_missing_values")
    si.run_method("calculate_taxes_and_totals")
    return si


@frappe.whitelist()
def get_sales_invoice_items_from_projects(projects: list[str] | str):
    """Return a set of Sales Invoice Item rows aggregated from the given projects.
    Uses each Project's sales_order, sku_producto and cantidad_a_producir.
    """
    import json

    if isinstance(projects, str):
        try:
            projects = json.loads(projects)
        except Exception:
            projects = [p.strip() for p in projects.split(',') if p.strip()]

    items = []
    errors = []

    for prj in projects or []:
        try:
            proj = frappe.get_doc("Project", prj)
            if not getattr(proj, 'sales_order', None):
                errors.append(_(f"Project {prj} has no linked Sales Order."))
                continue
            if not getattr(proj, 'sku_producto', None):
                errors.append(_(f"Project {prj} has no sku_producto set."))
                continue
            qty = flt(getattr(proj, 'cantidad_a_producir', 0))
            if qty <= 0:
                errors.append(_(f"Project {prj} has no valid quantity (cantidad_a_producir)."))
                continue

            # si = make_sales_invoice_from_project(proj.name, proj.sku_producto, qty)
            frappe.flags.args = frappe._dict({
                "project": proj.name,
                "item_code": proj.sku_producto,
                "qty": qty,
                "sales_order": proj.sales_order,
            })
            si = make_sales_invoice_from_project(proj.name)
            if si.items:
                row = si.items[0].as_dict()
                # Avoid conflicting primary keys on client insert
                row.pop('name', None)
                row.pop('owner', None)
                row.pop('idx', None)
                items.append(row)
        except Exception as e:
            errors.append(f"{prj}: {frappe.get_traceback() if frappe.conf.developer_mode else str(e)}")

    return {"items": items, "errors": errors}


@frappe.whitelist()
def get_delivery_note_items_from_projects(projects: list[str] | str):
    """Return a set of Delivery Note Item rows aggregated from the given projects.
    Uses each Project's sales_order, sku_producto and cantidad_a_producir.
    """
    import json

    if isinstance(projects, str):
        try:
            projects = json.loads(projects)
        except Exception:
            projects = [p.strip() for p in projects.split(',') if p.strip()]

    items = []
    errors = []

    for prj in projects or []:
        try:
            proj = frappe.get_doc("Project", prj)
            if not getattr(proj, 'sales_order', None):
                errors.append(_(f"Project {prj} has no linked Sales Order."))
                continue
            if not getattr(proj, 'sku_producto', None):
                errors.append(_(f"Project {prj} has no sku_producto set."))
                continue
            qty = flt(getattr(proj, 'cantidad_a_producir', 0))
            if qty <= 0:
                errors.append(_(f"Project {prj} has no valid quantity (cantidad_a_producir)."))
                continue

            dn = make_delivery_note_from_project(proj.name, proj.sku_producto, qty)
            if dn.items:
                row = dn.items[0].as_dict()
                row.pop('name', None)
                row.pop('owner', None)
                row.pop('idx', None)
                items.append(row)
        except Exception as e:
            errors.append(f"{prj}: {frappe.get_traceback() if frappe.conf.developer_mode else str(e)}")

    return {"items": items, "errors": errors}
