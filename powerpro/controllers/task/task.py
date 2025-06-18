# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Task(Document):
    def validate(self):
        self.validate_dependency_rules()
        self.validate_group_rules()

    def validate_dependency_rules(self):
        for dep in self.depends_on:
            if dep.task == self.name:
                frappe.throw("Una tarea no puede depender de sí misma.")

            if frappe.db.get_value("Task", dep.task, "is_group"):
                frappe.throw(f"No se puede depender de una tarea grupo: {dep.task}")

    def validate_group_rules(self):
        if self.is_group:
            if self.depends_on:
                frappe.throw("Las tareas grupo no pueden tener dependencias.")

            if self.users:
                frappe.throw("Las tareas grupo no deben tener responsables.")
