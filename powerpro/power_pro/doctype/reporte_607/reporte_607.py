# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva, SRL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cstr, cint, flt, formatdate, format_datetime
from frappe.model.document import Document
from frappe.utils.csvutils import UnicodeWriter
import time


class ReferenceNotFound(Exception):
    pass


class Reporte607(Document):
    pass


@frappe.whitelist()
def get_file_address(from_date, to_date, company):
    # AND sinv.posting_date BETWEEN '%s' AND '%s' """ % ("SINV-%", from_date, to_date), as_dict=True)
    result = frappe.db.sql(f"""
		SELECT 
            sinv.company,
			cust.tax_id,
			cust.tipo_rnc,
			sinv.ncf,
			sinv.return_against_ncf,
			sinv.tipo_de_ingreso,
			sinv.posting_date,
			(SELECT posting_date FROM `viewRetention By Invoice` WHERE reference_name = sinv.name) AS payment_date,
			sinv.base_net_total,
			sinv.base_grand_total,
			sinv.base_total_taxes_and_charges,
			(SELECT COALESCE(retention_amount, '') FROM `viewRetention By Invoice` WHERE reference_name = sinv.name) AS retention_amount,
			0 as itbis_percibido,
			0 as retention_renta_terceros,
			0 as isr_percibido,
            per.isr_category,
            SUM(per.isr_amount),
			0 as impuesto_selectivo_al_consumo,
			0 as otros_impuestos_y_tasas,
			0 as monto_propina_legal,
			(SELECT cash_payment from `view607 Payments` WHERE sinv_name = sinv.name) as cash_payment,
			(SELECT bank_payment from `view607 Payments` WHERE sinv_name = sinv.name) as bank_payment,
			(SELECT cc_payment from `view607 Payments` WHERE sinv_name = sinv.name) as cc_payment,
			(SELECT credit from `view607 Payments` WHERE sinv_name = 'sinv.name') as credit,
			0 bonos_regalo,
			0 permuta_de_pago,
			0 otros
		FROM 
        	`tabSales Invoice` AS sinv 
		INNER JOIN 
        	`tabCustomer` AS cust 
        ON 
        	sinv.customer = cust.name 
        LEFT JOIN
            `tabPayment Entry Reference` AS per
        ON
            per.reference_name = sinv.name
        LEFT JOIN
            `tabPayment Entry` AS pe
        ON
            pe.name = per.parent
		WHERE 
            sinv.docstatus = 1  AND sinv.company = {company!r}
            AND sinv.posting_date BETWEEN {from_date!r} AND {to_date!r}
        	OR pe.posting_date BETWEEN {from_date!r} AND {to_date!r}
            AND per.retention_amount > 0
            AND per.isr_amount > 0
           
        GROUP BY 
            sinv.name
	""", as_dict=True)
    #sinv.ncf NOT LIKE '%s'
    #AND cust.tax_id > 0 
    w = UnicodeWriter()
    w.writerow([
        'Company',
        'RNC/Cedula o Pasaporte',               									# 0
        'Tipo de Identificacion',      												# 1
        'Numero de Comprobante Fiscal',         									# 2
        'Numero de Comprobante Fiscal modificado', 									# 3
        'Tipo de Ingreso', 															# 4
        'Fecha de Comprobante',														# 5
        'Fecha de Retencion',														# 6
        'Monto Facturado',															# 7
        'ITBIS Facturado',															# 8
        'ITBIS Retenido por Terceros',             									# 9
        'ITBIS Percibido',															# 10
        'Retencion Renta por Terceros',												# 11
        'ISR Percibido',
        'ISR Categoria',															# 12
        'Monto ISR',
        'Impuesto Selectivo al Consumo',											# 13
        'Otros Impuestos y Tasas',													# 14
        'Monto Propina Legal',														# 15
        'Efectivo',																	# 16
        'Cheque/Transferencia/Deposito',											# 17
        'Tarjeta de Debito/Credito',												# 18
        'Venta Credito',															# 19
        'Bonos o Certificados de Regalo',											# 20
        'Permuta',																	# 21
        'Otras Formas de Venta'														# 22
    ])

    for row in result:
        w.writerow([
            # 0
            row.company,
            cstr(row.tax_id).replace("-", ""),
            row.tipo_rnc,															# 1
            row.ncf,																# 2
            row.return_against_ncf,													# 3
            row.tipo_de_ingreso,													# 4
            row.posting_date.strftime("%Y%m%d"),									# 5
            # 6   row.payment_date.strftime("%Y%m%d") if row.payment_date  else "",
            get_retention_date(row),
            row.base_net_total,														# 7
            row.base_total_taxes_and_charges,										# 8
            # 9   row.retention_amount,
            get_retention_amount(row, typeof="ITBIS", from_date=from_date),
            row.itbis_percibido or "",												# 10
            # 11  row.retention_renta_terceros,
            get_retention_amount(row, typeof="ISR", from_date=from_date),
            row.isr_percibido or "",												# 12
            row.isr_category,
            row.isr_amount or 0,
            row.impuesto_selectivo_al_consumo,										# 13
            row.otros_impuestos_y_tasas,											# 14
            row.monto_propina_legal,												# 15
            row.cash_payment or .00,												# 16
            row.bank_payment or .00,												# 17
            row.cc_payment or .00,													# 18
            row.credit or row.base_grand_total,										# 19
            row.bonos_regalo or .00,												# 20
            row.permuta_de_pago or .00,												# 21
            row.otros or .00														# 22
        ])

    frappe.response['result'] = cstr(w.getvalue())
    frappe.response['type'] = 'csv'
    frappe.response['doctype'] = "Reporte_607_" + str(int(time.time()))


def get_retention_date(row):
    try:
        reference_row = get_reference_row(row)
    except ReferenceNotFound:
        return 0
    else:
        posting_date = frappe.get_value(
            "Payment Entry", reference_row.parent, "posting_date")
        return frappe.utils.getdate(posting_date).strftime("%Y%m")


def get_retention_amount(row, typeof, from_date):
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
    else:
        return reference_row.retention_amount


def get_retention_type(row):
    # will return the retention_category of the retention selected in the Payment Entry
    # if set, else will return empty string
    try:
        reference_row = get_reference_row(row, typeof="ISR")
    except ReferenceNotFound:
        return ""
    else:
        return reference_row.retention_category


def get_reference_row(row, typeof=None):
    # will return the row of the Payment Entry that has the same reference as the Purchase Invoice
    # if set, else will return empty string
    doctype = "Payment Entry Reference"
    filters = {
        "reference_doctype": "Purchase Invoice",
        "reference_name": row.name,
        # "doctatus": "1",
    }

    if typeof is not None:
        filters["retention_type"] = typeof

    if frappe.db.exists(doctype, filters):
        return frappe.get_doc(doctype, filters)

    raise ReferenceNotFound()
