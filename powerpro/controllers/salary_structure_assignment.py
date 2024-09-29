# Copyright (c) 2024, Miguel Higuera and Contributors
# For license information, please see license.txt


import frappe
from frappe import _


def validate(doc, method):
    calculate_salary_per_hour(doc)
    validate_deduct_on(doc)


def calculate_salary_per_hour(doc):
    salary_per_hour = doc.base / 23.83 / 8
    doc.salary_per_hour = round(salary_per_hour, 2)


def validate_deduct_on(doc):
    if not doc.include_transportation:
        doc.transportation_fee = 0
        doc.deduct_on = None
        return

    salary_structure = get_salary_structure(doc.salary_structure)

    if salary_structure.payroll_frequency == "Monthly" \
            and doc.deduct_on != "Transport Deduct on 30th Day":
        frappe.throw(_("Deduct on must be 'Transport Deduct on 30th Day' for Monthly payroll period."))


def get_salary_structure(salary_structure):
    doctype = "Salary Structure"
    return frappe.get_doc(doctype, salary_structure)
