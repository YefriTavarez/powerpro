# Copyright (c) 2024, Miguel Higuera And contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe.utils import cstr, cint, flt, formatdate, format_datetime
from frappe.model.document import Document
from frappe.utils.csvutils import UnicodeWriter
import time
from frappe import _


class Reporte609(Document):
    pass
 

@frappe.whitelist()
def get_file_address(from_date, to_date):
    result = frappe.db.sql(f"""
    Select 
        purchase_invoice.name,
        purchase_invoice.supplier,
        supplier.type_of_tax_identification,
        purchase_invoice.tax_id,
        purchase_invoice.country_code,
        purchase_invoice.type_of_service_purchased,
        purchase_invoice.details_of_service_purchased,
        payment_entry_reference.related_part,
        payment_entry_reference.reference_name,
        purchase_invoice.posting_date,
        payment_entry_reference.allocated_amount,
        purchase_invoice.isr_date,
        purchase_invoice.retention_amount,
        purchase_invoice.isr_amount,
        Case 
            When payment_entry.posting_date Between {from_date!r} And {to_date!r} Then purchase_invoice.retention_amount
            Else 0
        End AS retention_amount,
        Case
            When payment_entry.posting_date <> purchase_invoice.posting_date And purchase_invoice.retention_amount > 0 Then 1
            Else 0
        End AS show_in_other_month_report
    From 
        `tabPurchase Invoice` AS purchase_invoice
    Left Join
        `tabSupplier` AS supplier
    ON
        purchase_invoice.supplier = supplier.name
    Left Join
        `tabPayment Entry Reference` AS payment_entry_reference
    ON
        purchase_invoice.name = payment_entry_reference.reference_name
    Left Join
        `tabPayment Entry` AS payment_entry
    ON
        payment_entry_reference.parent = payment_entry.name
    WHERE 
        purchase_invoice.docstatus = 1
        And payment_entry.docstatus = 1
        And payment_entry.posting_date Between {from_date!r} And {to_date!r}
        And payment_entry_reference.allocated_amount > 0
    """, as_dict=True)

    w = UnicodeWriter()
    w.writerow([
		"Nombre o Razón Social",
        "Tipo ID Tributaria",
        "ID Tributaria",
        "País de Destino",
        "Tipo de Servicio adquirido",
        "Detalle del Servicio adquirido",
        "Parte relacionada",
        "Número de Documento",
        "Fecha de Documento",
        "Monto Facturado",
        "Fecha de Retención ISR",
        "Renta Presunta",
        "ISR Retenido",
    ])

    for row in result:
        w.writerow([
            row.supplier,
            row.type_of_tax_identification,
            row.tax_id,
            row.country_code,
            row.type_of_service_purchased,
            row.details_of_service_purchased,
            row.related_part,
            row.reference_name,
            row.posting_date,
            row.allocated_amount,
            row.isr_date,
            row.retention_amount,
            row.isr_amount,
        ])

    frappe.response['result'] = cstr(w.getvalue())
    frappe.response['type'] = 'csv'
    frappe.response['doctype'] = "Reporte_609_" + str(int(time.time()))


