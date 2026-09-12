"""Explicit source identity shared by evidence elections, credits and audit rows."""
import frappe
from frappe import _

AUTH='Overtime Authorization'
RETRO='Retroactive Overtime Adjustment'


def evidence_enabled(doc):
    return bool(doc.get('evidence_enrolled')) if doc.doctype==AUTH else (
        doc.doctype==RETRO and doc.get('reconciliation_engine')=='Verified Checkins')


def links(doc,*,authorization_field='authorization'):
    if doc.doctype not in {AUTH,RETRO}:
        frappe.throw(_('Origen de horas extra no admitido.'))
    return {authorization_field:doc.name} if doc.doctype==AUTH else {'retroactive_adjustment':doc.name}


def identity(row,*,authorization_field='authorization'):
    auth=row.get(authorization_field);retro=row.get('retroactive_adjustment')
    if bool(auth)==bool(retro):
        frappe.throw(_('Indique exactamente una autorización o un ajuste retroactivo como origen.'))
    return (AUTH,auth) if auth else (RETRO,retro)


def get_source(row,*,for_update=False):
    return frappe.get_doc(*identity(row),for_update=for_update)


def claim(doc):
    # Keep existing authorization claims unchanged; retroactive names are scoped.
    return doc.name if doc.doctype==AUTH else RETRO+'|'+doc.name
