"""Install the exclusion snapshot and seed the requested freelancer structure once."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields({"Salary Slip": [{
        "fieldname": "employer_contributions_excluded",
        "fieldtype": "Check",
        "label": "Excluido de aportes del empleador",
        "insert_after": "employer_contributions_tab",
        "read_only": 1,
        "no_copy": 1,
        "default": "0",
        "description": "Según la estructura salarial al calcular este recibo. Las deducciones del empleado se conservan.",
    }]}, update=True)
    settings = frappe.get_single("DGII Payroll Settings")
    structure = "General Iguala"
    if frappe.db.exists("Salary Structure", structure) and not any(
        row.salary_structure == structure
        for row in settings.get("employer_contribution_exclusions", [])
    ):
        settings.append("employer_contribution_exclusions", {"salary_structure": structure})
        settings.save(ignore_permissions=True)
    frappe.clear_cache(doctype="Salary Slip")
    frappe.clear_cache(doctype="DGII Payroll Settings")
