# Copyright (c) 2026, PowerPro contributors
# For license information, please see license.txt

"""Add the employee metadata required by Banco Popular's payroll layout.

The fields are intentionally optional at the DocType level so this patch does
not block edits to existing Employee records. Payroll Bank Batch validation is
the enforcement point and will refuse to approve incomplete bank instructions.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields(
        {
            "Employee": [
                {
                    "fieldname": "custom_bank_account_type",
                    "label": "Tipo de cuenta bancaria",
                    "fieldtype": "Select",
                    "options": "\nAhorro\nCorriente",
                    "insert_after": "bank_ac_no",
                    "description": (
                        "Requerido para generar archivos de nómina del Banco Popular."
                    ),
                },
                {
                    "fieldname": "custom_bank_identification_type",
                    "label": "Tipo de identificación bancaria",
                    "fieldtype": "Select",
                    "options": "Cédula\nPasaporte\nRNC",
                    "default": "Cédula",
                    "insert_after": "custom_bank_account_type",
                    "description": (
                        "Tipo del documento de identidad incluido en el archivo bancario."
                    ),
                },
                {
                    "fieldname": "custom_bank_identification_number",
                    "label": "Identificación bancaria",
                    "fieldtype": "Data",
                    "insert_after": "custom_bank_identification_type",
                    "description": (
                        "Cédula, pasaporte o RNC incluido en el archivo bancario. "
                        "Si queda vacío, PowerPro usa la identificación personal existente."
                    ),
                },
            ]
        },
        update=True,
    )
    frappe.clear_cache(doctype="Employee")
