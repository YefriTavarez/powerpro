# Copyright (c) 2024, Rainier Polanco and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cstr, flt, cint, getdate
from frappe.model.document import Document
from frappe.utils.csvutils import UnicodeWriter
import time
from frappe import _

from .utils import tax_id_type_map, good_service_type_map
from . import helper

DGII_DATE_FORMAT = "%Y%m%d"  # AAAAMMDD

class Reporte606(Document):
    pass
 

class ReferenceNotFound(Exception):
    pass


@frappe.whitelist()
def get_file_address(from_date, to_date, txt=0):
    result = frappe.db.sql(f"""
        Select
            pinv.name As name,
            pinv.supplier As supplier,
            pinv.tax_id As tax_id,
            NULL As tipo_rnc,
            pinv.tipo_bienes_y_servicios_comprados As tipo_bienes_y_servicios_comprados,
            pinv.ncf As ncf,
            NULL As ncf_modificado,
            pinv.posting_date As posting_date,
            NULL As fecha_pago,
            Sum(
                If (
                    IfNull(pinvitm.item_type, "") != "Bienes",
                    Abs(pinvitm.base_amount),
                    0
                )
            ) As monto_facturado_servicios,
            Sum(
                If (
                    IfNull(pinvitm.item_type, "") = "Bienes",
                    Abs(pinvitm.base_amount),
                    0
                )
            ) As monto_facturado_bienes,
            NULL As monto_facturado_total,
            NULL As itbis_facturado,
            NULL As itbis_retenido,
            NULL As itbis_sujeto_a_proporcionalidad,
            NULL As itbis_llevado_al_costo,
            NULL As itbis_por_adelantar,
            NULL As itbis_percibido_en_compras,
            NULL As tipo_de_retencion_en_isr,
            NULL As monto_retencion_renta,
            NULL As isr_percibido_en_compras,
            NULL As impuesto_selectivo_al_consumo,
            NULL As otros_impuesto_tasas,
            NULL As monto_propina_legal,
            NULL As forma_de_pago
        From
            `tabPurchase Invoice` As pinv
        Inner Join
            `tabPurchase Invoice Item` As pinvitm
            On pinvitm.parent = pinv.name
            And pinvitm.parenttype = 'Purchase Invoice'
            And pinvitm.parentfield = 'items'
            And pinvitm.docstatus = pinv.docstatus
        Where
            pinv.posting_date Between {from_date!r} And {to_date!r}
            And pinv.docstatus = 1
            And pinv.ncf Is Not Null
            And pinv.ncf != ''
            Or (
                pinv.taxes_and_charges_deducted != 0
                And pinv.name In (
                    Select
                        ref.reference_name
                    From
                        `tabPayment Entry Reference` As ref
                    Inner Join
                        `tabPayment Entry` As pe
                        On pe.name = ref.parent
                    Where
                        ref.reference_doctype = 'Purchase Invoice'
                        And pe.docstatus = 1
                        And pe.posting_date Between {from_date!r} And {to_date!r}
                )
                And pinv.posting_date <= {to_date!r} # ensure not future invoices to this range
            )
        Group By
            pinv.name
	""", as_dict=True, debug=True)
    
    if cint(txt) == 1:
        content = generate_txt(result, from_date, to_date)
        frappe.response['result'] = cstr(content)
        frappe.response['type'] = 'txt'
    else:
        w = UnicodeWriter()
        w.writerow([
            'RNC o Cedula',                                                    #01
            'Tipo Id',                                                         #02
            'Tipo Bienes y Servicios Comprados',                               #03
            'NCF',                                                             #04
            'NCF Modificado',                                                   #05
            'Fecha Comprobante',                                               #06
            'Dia',                                                             #06
            'Fecha Pago',                                                      #07
            'Dia',                                                             #07
            'Monto Facturado en Servicios',                                    #08
            'Monto Facturado en Bienes',                                       #09
            'Total Monto Facturado',                                           #10
            'ITBIS Facturado',                                                 #11
            'ITBIS Retenido',                                                  #12
            'ITBIS sujeto a Proporcionalidad (Art. 349)',                      #13
            'ITBIS llevado al Costo',                                          #14
            'ITBIS por Adelantar',                                             #15
            'ITBIS percibido en compras',                                      #16
            'Tipo de Retencion en ISR',                                        #17
            'Monto Retención Renta',                                           #18
            'ISR Percibido en compras',                                        #19
            'Impuesto Selectivo al Consumo',                                   #20
            'Otros Impuesto/Tasas',                                            #21
            'Monto Propina Legal',                                             #22
            'Forma de Pago',                                                   #23                            
        ])

        for row in result:
            _posting_date = ''
            _posting_day = ''

            _payment_date = ''
            _payment_day = ''

            if date := row.posting_date:
                _posting_date = date.strftime("%Y%m")
                _posting_day = date.strftime("%d")

            if date := get_retention_date_if_in_range(row, from_date, to_date):
                _payment_date = date.strftime("%Y%m")
                _payment_day = date.strftime("%d")

            if not row.tax_id:
                row.tax_id = frappe.get_value("Supplier", row.supplier, "tax_id")
            
            if not row.tax_id:
                frappe.throw(_("Tax ID not found for supplier {0}").format(row.supplier))

            row.tax_id = row.tax_id.replace("-", "")

            selectivo_facturado = helper.get_selectivo_facturado(from_date=from_date, to_date=to_date, invoice_id=row.name)
            otros_imp_facturado = helper.get_otros_imp_facturado(from_date=from_date, to_date=to_date, invoice_id=row.name)
            propina_facturada = helper.get_propina_facturada(from_date=from_date, to_date=to_date, invoice_id=row.name)

            impuestos_combinados = flt(selectivo_facturado) + flt(otros_imp_facturado) + flt(propina_facturada)


            write_row = [
                row.tax_id if row.tax_id else "", 	# RNC                                                #01
                helper.get_tipo_rnc(row),                                                                                            #02        
                helper.get_tipo_bienes_y_servicios_comprados(row),        # Tipo de RNC                                              #03 row.ncf,		# NCF                                                                                    #04
                row.ncf,                                                                                                 #04
                helper.get_ncf_modificado(from_date=from_date, to_date=to_date, invoice_id=row.name),		              #05
                _posting_date,  # FC AAAAMM                                                                              #06
                _posting_day,   # FC AAAAMM                                                                              #06
                _payment_date,  # FC AAAAMM                                                                              #07
                _payment_day,   # FC AAAAMM                                                                              #07
                flt(row.monto_facturado_servicios),  # Monto Facturado en Servicios                                           #08 Esta + get_selectivo_facturado + get_otros_imp_facturado + get_propina_facturada
                flt(row.monto_facturado_bienes),	# Monto Facturado en bienes                                                  #09 Esta + get_selectivo_facturado + get_otros_imp_facturado + get_propina_facturada
                flt(row.monto_facturado_servicios) + flt(row.monto_facturado_bienes) + impuestos_combinados,                                      #10 Esta + get_selectivo_facturado + get_otros_imp_facturado + get_propina_facturada
                helper.get_itbis_facturado(from_date=from_date, to_date=to_date, invoice_id=row.name),                   #11
                helper.get_itbis_retenido(from_date=from_date, to_date=to_date, invoice_id=row.name),                    #12
                helper.get_itbis_sujeto_proporcionalidad(from_date=from_date, to_date=to_date, invoice_id=row.name),     #13
                helper.get_itbis_llevado_costo(from_date=from_date, to_date=to_date, invoice_id=row.name),               #14
                helper.get_itbis_adelantado(from_date=from_date, to_date=to_date, invoice_id=row.name),                  #15
                helper.get_itbis_percibido(from_date=from_date, to_date=to_date, invoice_id=row.name),                   #16
                helper.get_tipo_retencion_isr(from_date=from_date, to_date=to_date, invoice_id=row.name),                #17
                helper.get_isr_retenido(from_date=from_date, to_date=to_date, invoice_id=row.name),                      #18
                helper.get_isr_percibido(from_date=from_date, to_date=to_date, invoice_id=row.name),                     #19
                selectivo_facturado,               #20
                otros_imp_facturado,               #21
                propina_facturada,                 #22
                helper.get_forma_de_pago(from_date=from_date, to_date=to_date, invoice_id=row.name),                     #23
            ]

            if ncf := row.get("ncf"):
                # handle credit notes
                if ncf.startswith("B04") \
                    or ncf.startswith("E34"):
                    # credit notes should always be positive numbers,
                    # however a credit note in ERPNext is just an invoice with a negative amount
                    # so we need to make the amount positive
                    for index, element in enumerate( write_row.copy() ):
                        # if element is a numeric value, make it positive
                        if isinstance( element, (int, float) ):
                            write_row[index] = abs(element)

            w.writerow(write_row)

        frappe.response['result'] = cstr(w.getvalue())
        frappe.response['type'] = 'csv'

    # result and type are dynamic, so, yes, this line is correctly indented
    frappe.response['doctype'] = "Reporte_606_" + str(int(time.time()))

def generate_txt(result, from_date, to_date):
    # load company details
    company_id = frappe.defaults.get_global_default("company")
    company = frappe.get_doc("Company", company_id)
    buyer_tax_id = company.tax_id


    # date of the report
    month_date = getdate(from_date).strftime("%Y%m")


    # header of text file
    lines = [
        f"606|{buyer_tax_id.replace('-', '')}|{month_date}|{str(len(result))}",  # 1
    ]
    for row in result:
        # Prepare date fields as in CSV generation
        _posting_date_aaaammdd = ""
        if row.posting_date:
            _posting_date_aaaammdd = row.posting_date.strftime("%Y%m%d")

        _payment_date_obj = get_retention_date_if_in_range(row, from_date, to_date)
        _payment_date_aaaammdd = ""
        if _payment_date_obj:  # If it's a date object and not an empty string
            # Assuming _payment_date_obj is a date object if not empty string
            try:
                _payment_date_aaaammdd = _payment_date_obj.strftime("%Y%m%d")
            except AttributeError: # Handles case where _payment_date_obj might be "" or other non-date
                pass


        if not row.tax_id:
            row.tax_id = frappe.get_value("Supplier", row.supplier, "tax_id")
        
        if not row.tax_id:
            frappe.throw(_("Tax ID not found for supplier {0}").format(row.supplier))

        row.tax_id = row.tax_id.replace("-", "")



        selectivo_facturado = helper.get_selectivo_facturado(from_date=from_date, to_date=to_date, invoice_id=row.name)
        otros_imp_facturado = helper.get_otros_imp_facturado(from_date=from_date, to_date=to_date, invoice_id=row.name)
        propina_facturada = helper.get_propina_facturada(from_date=from_date, to_date=to_date, invoice_id=row.name)

        impuestos_combinados = flt(selectivo_facturado) + flt(otros_imp_facturado) + flt(propina_facturada)


        line = (
            f"{row.tax_id if row.tax_id else ''}|"  # 1
            f"{helper.get_tipo_rnc(row) or ''}|"  # 2
            f"{helper.get_tipo_bienes_y_servicios_comprados(row) or ''}|"  # 3
            f"{row.ncf or ''}|"  # 4
            f"{helper.get_ncf_modificado(from_date=from_date, to_date=to_date, invoice_id=row.name)}|"  # 5
            f"{_posting_date_aaaammdd}|"  # 6
            f"{_payment_date_aaaammdd}|"  # 8
            f"{flt(row.monto_facturado_servicios) + flt(impuestos_combinados, 2)}|"  # 10
            f"{flt(row.monto_facturado_bienes, 2)}|"  # 11
            f"{flt(row.monto_facturado_servicios, 2) + flt(row.monto_facturado_bienes, 2) + flt(impuestos_combinados, 2)}|"  # 12
            f"{helper.get_itbis_facturado(from_date=from_date, to_date=to_date, invoice_id=row.name) or 0}|"  # 13
            f"{helper.get_itbis_retenido(from_date=from_date, to_date=to_date, invoice_id=row.name) or 0}|"  # 14
            f"{helper.get_itbis_sujeto_proporcionalidad(from_date=from_date, to_date=to_date, invoice_id=row.name) or 0}|"  # 15
            f"{helper.get_itbis_llevado_costo(from_date=from_date, to_date=to_date, invoice_id=row.name) or 0}|"  # 16
            f"{helper.get_itbis_adelantado(from_date=from_date, to_date=to_date, invoice_id=row.name) or 0}|"  # 17
            f"{helper.get_itbis_percibido(from_date=from_date, to_date=to_date, invoice_id=row.name) or 0}|"  # 18
            f"{helper.get_tipo_retencion_isr(from_date=from_date, to_date=to_date, invoice_id=row.name) or ''}|"  # 19
            f"{helper.get_isr_retenido(from_date=from_date, to_date=to_date, invoice_id=row.name) or 0}|"  # 20
            f"{helper.get_isr_percibido(from_date=from_date, to_date=to_date, invoice_id=row.name) or 0}|"  # 21
            f"{helper.get_selectivo_facturado(from_date=from_date, to_date=to_date, invoice_id=row.name) or 0}|"  # 22
            f"{helper.get_otros_imp_facturado(from_date=from_date, to_date=to_date, invoice_id=row.name) or 0}|"  # 23
            f"{helper.get_propina_facturada(from_date=from_date, to_date=to_date, invoice_id=row.name) or 0}|"  # 24
            f"{helper.get_forma_de_pago(from_date=from_date, to_date=to_date, invoice_id=row.name) or ''}"  # 25
        )
        
        lines.append(line)
    
    return "\n".join(lines)

def get_retention_date(row):
    try:
        reference_row = get_reference_row(row)
    except ReferenceNotFound:
        return 0
    # else:
    posting_date = frappe.get_value(
            "Payment Entry", reference_row.parent, "posting_date")
    return frappe.utils.getdate(posting_date).strftime("%Y%m")


def get_retention_amount(row, from_date, typeof):
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
    accounts_for_itbis = []

    doc = frappe.get_doc("Purchase Invoice", row.name)
    for item in doc.taxes:
        if item.account_head in accounts_for_itbis:
            return item.base_tax_amount

def get_itbis(row):
    conf = frappe.get_doc("DGII Settings")

    doctype = "Purchase Invoice"
    doc = frappe.get_doc(doctype, row.name)
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
        
        if from_date <= row.isr_date <= to_date:
            return row.isr_date  
            
    return ""  


def get_retention_date_if_in_range(row, from_date, to_date):
    if row.retention_date:
        if from_date <= row.retention_date <= to_date:
            return row.retention_date  

    return ""  


@frappe.whitelist()
def get_summary_data(from_date, to_date):
    data = frappe.db.sql(f"""
        Select
            Sum(pinv.base_total) as subtotal,
            Sum(
                Case 
                    When IfNull(account.dominican_tax_type, "") = "ITBIS" and IfNull(taxes.add_deduct_tax, "") = "Add" Then taxes.tax_amount
                    Else 0
                End
            ) as itbis
        From
            `tabPurchase Invoice` as pinv
        Left Join
            `tabPurchase Taxes and Charges` As taxes
            On taxes.parent = pinv.name
            And taxes.parenttype = 'Purchase Invoice'
            And taxes.parentfield = 'taxes'
            And taxes.docstatus = pinv.docstatus
        Left Join
            `tabAccount` As account
            On account.name = taxes.account_head
        Where
            pinv.posting_date Between {from_date!r} And {to_date!r}
            And pinv.docstatus = 1
            And Left(pinv.ncf, 3) In ("B01", "B03", "B04", "B11", "B13", "B14", "B15", "E31", "E33", "E34", "E41", "E43")
    """, as_dict=True)

    return data[0] if data else {}
