# Copyright (c) 2024, Miguel Higuera and Contributors
# For license information, please see license.txt

import frappe
from frappe.utils import cint


def before_insert(doc, method):
    delete_ncf(doc)
    set_return_against_ncf(doc)
    delete_cancellation_type(doc)


def on_submit(doc, method):
    set_ncf(doc)


def on_cancel(doc, method):
    validate_cancellation_type(doc)


def delete_ncf(doc):
    if doc.informal_customer:
        return

    if doc.amended_from:
        return False

    if doc.ncf and not doc.is_return:
        doc.ncf = None


def set_return_against_ncf(doc):
    if doc.ncf and doc.is_return:
        doc.return_against_ncf = doc.ncf
        doc.ncf = None


def set_ncf(doc):
    if doc.informal_customer:
        return

    if not doc.naming_series:
        return False

    if doc.amended_from:
        return False

    # if doc.is_pos and doc.ncf:
    #     return False

    if doc.ncf and not doc.is_return:
        return False

    ncf_manager = get_serie(doc)

    if not ncf_manager.serie:
        return ''
    current = cint(ncf_manager.current)

    if cint(ncf_manager.top) and current >= cint(ncf_manager.top):
        frappe.throw(
            "Se ha alcanzado el limite de comprobantes para esta serie."
        )

    current += 1

    ncf_manager.current = current
    ncf_manager.db_update()
    # doc.ncf = '{0}{1:08d}'.format(ncf_manager.serie.split(".")[0], current)
    doc.db_set("ncf", '{0}{1:08d}'.format(ncf_manager.serie.split(".")[0], current))


def get_serie(doc):
    if not doc.tax_category:
        doc.tax_category = get_customer_tax_category(doc)

        if not doc.tax_category:
            frappe.throw(
                "Seleccione una categoria de impuestos para el cliente antes de validar el documento."
            )

    if not doc.tax_category:
        frappe.throw(
            "Seleccione una categoria de impuestos para el cliente antes de validar el documento."
            )

    if doc.is_return:
        credit_note = get_credit_note(doc.company)
        if not credit_note:
            frappe.throw(
                "No se ha configurado una serie para las notas de credito."
                )

        doc.tax_category = credit_note.tax_category

        return credit_note

    return get_ncf_manager(doc)


def get_credit_note(company):
    doctype = "NCF Manager"
    filters = {
        "company": company,
        "serie": ["like", "B04%"]
    }

    return frappe.get_doc(doctype, filters)


def get_customer_tax_category(doc):
    doctype = "Customer"
    fieldname = "tax_category"

    return frappe.get_value(doctype, doc.customer, fieldname)


def get_ncf_manager(doc):
    doctype = "NCF Manager"
    filters = {
        "company": doc.company,
        "tax_category": doc.tax_category
    }

    if name := frappe.db.exists(doctype, filters):
        return frappe.get_doc(doctype, name)
    else:
        frappe.throw(
            f"No se ha configurado una serie para la categoria de impuestos <b>{doc.tax_category}</b>."
        )


def validate_cancellation_type(doc):
    if not doc.cancellation_type:
        frappe.throw(
            "Debe seleccionar un tipo de anulacion para cancelar el documento."
        )


def delete_cancellation_type(doc):
    if doc.amended_from:
        doc.cancellation_type = None