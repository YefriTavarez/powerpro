# Copyright (c) 2024, Miguel Higuera and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cstr, cint, flt, formatdate, format_datetime
from frappe.model.document import Document
from frappe.utils.csvutils import UnicodeWriter
import time


class Reporte623(Document):
    pass


@frappe.whitelist()
def get_file_address(from_date, to_date):
    data = f"""
        Select 
            supplier.tax_id,
            purchase_invoice.posting_date,
            purchase_invoice.retention_date,
            purchase_invoice.retention_amount,
            payment_entry.reference_no,
            payment_entry.mode_of_payment,
            bank_account.bank,
            purchase_invoice.status
        From
            `tabPurchase Invoice` As purchase_invoice
        Inner Join
            `tabSupplier` As supplier
        On
            purchase_invoice.supplier = supplier.name
        Inner Join
            `tabPayment Entry Reference` As payment_entry_reference
        On
            purchase_invoice.name = payment_entry_reference.reference_name
        Inner Join
            `tabPayment Entry` As payment_entry
        On
            payment_entry_reference.parent = payment_entry.name
        Inner Join
            `tabBank Account` As bank_account
        On
            payment_entry.bank_account = bank_account.name
        Where 
            purchase_invoice.docstatus = 1 And
            purchase_invoice.posting_date Between {from_date!r} And {to_date!r}
        """
    result = frappe.db.sql(data, as_dict=True)

    w = UnicodeWriter()
    w.writerow([
        "RNC Entidad del Estado",
        "Período",
        "Fecha de retención",
        "Valor de retención",
        "Número de Referencia",
        "Tipo de referencia", # Get the doctype name
        "Banco",
        "Estado",
    ])

    for row in result:
        # Dates in the format YYYYMM
        w.writerow([
            row.tax_id,
            format_datetime(row.posting_date, "yyyyMM"),
            format_datetime(row.retention_date, "yyyyMMdd"),
            row.retention_amount,
            row.reference_no,
            row.mode_of_payment,
            row.bank,
            "En Proceso" if row.status == "Draft" else "Completada" if row.status == "Paid" else "Activa"
        ])

    frappe.response["result"] = cstr(w.getvalue())
    frappe.response["type"] = "csv"
    frappe.response["doctype"] = "Reporte_623_" + str(int(time.time()))

