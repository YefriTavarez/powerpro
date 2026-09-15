"""Employer-only exclusions; submitted slips keep their calculation-time decision."""

import frappe


def is_excluded(doc):
    structure = doc.get("salary_structure")
    if not structure:
        return False
    settings = frappe.get_single("DGII Payroll Settings")
    return any(row.salary_structure == structure
               for row in settings.get("employer_contribution_exclusions", []))
