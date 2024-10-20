# Copyright (c) 2024, Rainier Polanco and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cstr, cint, flt, formatdate, format_datetime
from frappe.model.document import Document
from frappe.utils.csvutils import UnicodeWriter
from datetime import datetime
import time
from frappe import _


class Reporte606(Document):
    pass
 

class ReferenceNotFound(Exception):
    pass


@frappe.whitelist()
def get_file_address(from_date, to_date, company="INDUSTRIA GRÁFICA DEL CARIBE", file_type="csv"):
    result = frappe.db.sql(f"""
SELECT
    pinv.taxes_and_charges_added,
    pinv.posting_date,
    pinv.company,
    pinv.name,
    pinv.tax_id,
    supl.tipo_rnc,
    pinv.tipo_bienes_y_servicios_comprados,
    pinv.ncf,
    pinv.bill_date,
    pinv.excise_tax,
    pinv.base_taxes_and_charges_added,
    CASE 
        WHEN pe.posting_date BETWEEN {from_date!r} AND {to_date!r} THEN pinv.retention_amount
        ELSE 0
    END AS retention_amount,
    CASE
        WHEN pe.posting_date <> pinv.posting_date AND pinv.retention_amount > 0 THEN 1
        ELSE 0
    END AS show_in_other_month_report,
    pinv.retention_type,
    pinv.total_itbis,
    pinv.total_taxes_and_charges,
    pinv.other_taxes,
    pinv.itbis_retenido,
    pinv.legal_tip,
    pinv.base_grand_total,
    pinv.monto_facturado_servicios,
    pinv.net_total,
    pinv.monto_facturado_bienes,
    per.isr_category,
    pinv.mop,
    pinv.base_total_taxes_and_charges,
    pinv.isr_amount
FROM 
    `tabPurchase Invoice` AS pinv
INNER JOIN 
    `tabSupplier` AS supl ON supl.name = pinv.supplier
LEFT JOIN (
    SELECT 
        per.parent, 
        MAX(posting_date) AS last_payment_date
    FROM 
        `tabPayment Entry`
    LEFT JOIN
        `tabPayment Entry Reference` AS per ON per.parent = `tabPayment Entry`.name
    WHERE 
        `tabPayment Entry`.docstatus = 1
    GROUP BY 
        parent
) AS pe_last ON pe_last.parent = pinv.name
LEFT JOIN
    `tabPayment Entry` AS pe ON pe.name = pe_last.parent AND pe.posting_date = pe_last.last_payment_date
LEFT JOIN
    `tabPayment Entry Reference` AS per ON per.reference_name = pinv.name AND per.parent = pe.name
WHERE
    pinv.docstatus = 1
    AND pinv.company = {company!r}
    AND pinv.posting_date >= {from_date!r} AND pinv.posting_date <= {to_date!r}

UNION ALL

SELECT 
    pinv.taxes_and_charges_added,
    pe.posting_date,
    pe.company,
    pinv.name,
    pinv.tax_id,
    supl.tipo_rnc,
    pinv.tipo_bienes_y_servicios_comprados,
    pinv.ncf,
    pinv.bill_date,
    pinv.excise_tax,
    pinv.base_taxes_and_charges_added,
    pinv.retention_amount,
    pinv.isr_amount,
    pinv.retention_type,
    pinv.total_itbis,
    pinv.total_taxes_and_charges,
    pinv.other_taxes,
    pinv.itbis_retenido,
    pinv.legal_tip,
    pinv.base_grand_total,
    pinv.monto_facturado_servicios,
    pinv.monto_facturado_bienes,
    pinv.net_total,
    per.isr_category,
    pinv.mop,
    pinv.base_total_taxes_and_charges,
    pinv.isr_amount
FROM 
    `tabPayment Entry Reference` AS per
INNER JOIN
    `tabPayment Entry` AS pe ON pe.name = per.parent AND pe.company = {company!r}
LEFT JOIN
    `tabPurchase Invoice` AS pinv ON per.reference_name = pinv.name
LEFT JOIN
    `tabSupplier` AS supl ON supl.name = pinv.supplier
WHERE
    pinv.docstatus = 1
    AND per.docstatus = 1 
    AND pe.posting_date BETWEEN {from_date!r} AND {to_date!r}
    AND pinv.posting_date < {from_date!r}
    AND per.retention_amount > 0
    AND per.isr_amount > 0
	""", as_dict=True)
    
    if file_type == "txt":
        content = generate_txt(result)
        frappe.response['result'] = cstr(content)
        frappe.response['type'] = 'txt'
    else:
        w = UnicodeWriter()
        w.writerow([
            'Company',                                                         #01
            'RNC o Cedula',                                                    #02
            'Tipo Id',                                                         #03
            'Tipo Bienes y Servicios Comprados',                               #04
            'NCF',                                                             #05
            'Fecha Comprobante',                                               #06
            'Fecha Pago',                                                      #07
            'dia',                                                             #08
            'Monto Facturado en Servicios',                                    #09
            'Monto Facturado en Bienes',                                       #10
            'Total Monto Facturado',                                           #11
            'ITBIS Facturado',                                                 #12
            'ITBIS Retenido',                                                  #13
            'ITBIS por Adelantar',                                             #14
            'ITBIS percibido en compras',                                      #15
            'Tipo de Retencion en ISR',                                        #16
            'Impuesto Selectivo al Consumo',                                   #17
            'Otros Impuesto/Tasas',                                            #18
            'Monto Propina Legal',                                             #19
            'Forma de Pago',                                                   #20
                                                                            
        ])

        for row in result:
            ncf = ''
            date = ''
            day = ''

            if row.ncf:
                ncf = row.ncf.split(
                    "-")[1] if (len(row.ncf.split("-")) > 1) else row.ncf  # NCF-A1##% || A1##%

            if row.posting_date:
                date = row.posting_date.strftime("%d%Y%m")
                day = row.posting_date.strftime("%d")

            w.writerow([
                row.company,                                                                 #1
                row.tax_id.replace("-", "") if row.tax_id else "", 	# RNC                    #2
                row.tipo_rnc,                                                                #3         
                row.tipo_bienes_y_servicios_comprados,        # Tipo de RNC                  #4
                ncf,		# NCF                                                            #5
                date,  # FC AAAAMM                                                           #6
                day,                                                                         #7
                get_retention_date(row),  # FP DD          #fecha pago                       #8
                row.monto_facturado_servicios,  # Monto Facturado en Servicios               #9
                row.monto_facturado_bienes,	# Monto Facturado en bienes                      #10
                flt(row.monto_facturado_servicios) + flt(row.monto_facturado_bienes),        #11
                get_itbis(row) or 0,		     # ITBIS Facturado                           #12
                row.itbis_retenido or 0,                                                     #13
                get_itbis(row) or 0,             #itbis por adelantar                        #14
                row.retention_type if row.retention_type else '',   #tipo de retencion       #15
                row.isr_amount or 0,  			# Monto Retención Renta                      #16
                row.excise_tax or 0,  			# Impuesto Selectivo al Consumo              #17
                row.other_taxes or 0,  			# Otros Impuesto/Tasas                       #18
                row.legal_tip,  				# Monto Propina Legal                        #19
                verify_payment(row)						    # Forma de Pago                              #20
            ])

        frappe.response['result'] = cstr(w.getvalue())
        frappe.response['type'] = 'csv'
    frappe.response['doctype'] = "Reporte_606_" + str(int(time.time()))

def generate_txt(result):
    lines = []
    for row in result:
        ncf = row.ncf.split("-")[1] if row.ncf and len(row.ncf.split("-")) > 1 else row.ncf
        date = row.posting_date.strftime("%d%Y%m") if row.posting_date else ''
        day = row.posting_date.strftime("%d") if row.posting_date else ''
        
        line = (
            f"{row.company}|"
            f"{row.tax_id.replace('-', '') if row.tax_id else ''}|"
            f"{row.tipo_rnc}|"
            f"{row.tipo_bienes_y_servicios_comprados}|"
            f"{ncf}|"
            f"{date}|"
            f"{day}|"
            f"{get_retention_date(row)}|"
            f"{row.monto_facturado_servicios}|"
            f"{row.monto_facturado_bienes}|"
            f"{flt(row.monto_facturado_servicios) + flt(row.monto_facturado_bienes)}|"
            f"{get_itbis(row) or 0}|"
            f"{row.itbis_retenido or 0}|"
            f"{get_itbis(row) or 0}|"
            f"{row.retention_type or ''}|"
            f"{row.isr_amount or 0}|"
            f"{row.excise_tax or 0}|"
            f"{row.other_taxes or 0}|"
            f"{row.legal_tip}|"
            f"{verify_payment(row)}\n"
        )
        
        lines.append(line)
    
    return "".join(lines)

def get_retention_date(row):
    try:
        reference_row = get_reference_row(row)
    except ReferenceNotFound:
        return 0
    # else:
    posting_date = frappe.get_value(
            "Payment Entry", reference_row.parent, "posting_date")
    return frappe.utils.getdate(posting_date).strftime("%Y%m")


def get_retention_amount(row,  from_date, typeof):
    retention_date = get_retention_date(row)
    bill_date = frappe.utils.getdate(from_date).strftime("%Y%m")

    if retention_date == 0 or bill_date != retention_date:
        return 0

    if typeof not in ["ITBIS", "ISR"]:
        return 0

    try:
        reference_row = get_reference_row(row, typeof)
    except ReferenceNotFound:
        return 0
    # else:
    return reference_row.retention_amount


def get_retention_type(row):
    # will return the retention_category of the retention selected in the Payment Entry
    # if set, else will return empty string
    try:
        reference_row = get_reference_row(row, typeof="ISR")
    except ReferenceNotFound:
        return ""
    # else:
    return reference_row.retention_category


def get_reference_row(row, typeof=None):
    # will return the row of the Payment Entry that has the same reference as the Purchase Invoice
    # if set, else will return empty string
    doctype = "Payment Entry Reference"
    filters = {
        "reference_doctype": "Purchase Invoice",
        "reference_name": row.name,
        #"doctatus": "1",
    }

    if typeof is not None:
        filters["retention_type"] = typeof

    if frappe.db.exists(doctype, filters):
        return frappe.get_doc(doctype, filters)

    raise ReferenceNotFound()

def get_retention_itbis(row):
    accounts_for_itbis = [
    ]

    doc = frappe.get_doc("Purchase Invoice", row.name)
    for item in doc.taxes:
        if item.account_head in accounts_for_itbis:
            return item.base_tax_amount

def get_itbis(row):
    conf = frappe.get_doc("DGII Settings")

        
    doc = frappe.get_doc("Purchase Invoice", row.name)
    for item in doc.taxes:
        if item.account_head == conf.itbis_account:
            return item.base_tax_amount
        

def get_payments_entries(row=None):
    doctype = "Payment Entry Reference"
    filters = {
        "reference_doctype": "Purchase Invoice",
        "reference_name": row.name,
    }

    if frappe.db.exists(doctype, filters):
        return frappe.get_all(doctype, filters)
    return []


def verify_payment(row=None):
    per = get_payments_entries(row)
    
    if not per:
        return " "
    
    payment_types = []
    
    for entry in per:
        parent_payment_entry = frappe.db.get_value("Payment Entry Reference", entry['name'], "parent")
        payment_entry_doc = frappe.get_doc("Payment Entry", parent_payment_entry)
        payment_types.append(payment_entry_doc.mode_of_payment)
    
    if len(payment_types) == 1:
        return payment_types[0]
    # Si todos los tipos de pago en la lista son iguales, devuelve el primero
    elif all(payment == payment_types[0] for payment in payment_types):
        return payment_types[0]
    # Si hay una mezcla de tipos de pago, devuelve "Mixto"
    else:
        return "Mixto"

        

def get_isr_date_if_in_range(row, from_date, to_date):
    if row.isr_date:     
        isr_date = row.isr_date.strftime("%Y-%m-%d")   
        from_date = datetime.strptime(from_date, "%Y-%m-%d")
        to_date = datetime.strptime(to_date, "%Y-%m-%d")
        isr_date_dt = datetime.strptime(isr_date, "%Y-%m-%d")

        
        if from_date <= isr_date_dt <= to_date:
            return row.isr_date  
            
    return "No esta entrando"  

def get_retention_date_if_in_range(row, from_date, to_date):
    if row.retention_date:
        retention_date = row.retention_date.strftime("%Y-%m-%d")
        from_date = datetime.strptime(from_date, "%Y-%m-%d")
        to_date = datetime.strptime(to_date, "%Y-%m-%d")
        retention_date_dt = datetime.strptime(retention_date, "%Y-%m-%d")

        if from_date <= retention_date_dt <= to_date:
            return row.retention_date  

    return "No esta entrando"  


