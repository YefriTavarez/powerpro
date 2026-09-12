"""Effective policy selection. No policy is approved or enabled implicitly."""
from datetime import timedelta
import frappe
from frappe import _
from frappe.utils import get_datetime,getdate
from powerpro.controllers.overtime import _reconciliation_rows
from powerpro.payroll_rules.overtime_pay_policy import FIELDS,VERSION,validate_policy


def get_effective_policy(doc,*,for_update=False):
    start=getdate(doc.authorization_start)
    last=(get_datetime(doc.authorization_end)-timedelta(microseconds=1)).date()
    rows=_reconciliation_rows('Overtime Pay Policy',for_update=for_update,
        filters=[['company','=',doc.company],['docstatus','=',1],['valid_from','<=',last],['valid_until','>=',start]],
        fields=list(FIELDS),order_by='valid_from asc, name asc',limit=3)
    if not rows:return None
    if len(rows)!=1 or getdate(rows[0].valid_from)>start or getdate(rows[0].valid_until)<last:
        frappe.throw(_('La ventana debe estar cubierta por una sola política aprobada. Revise vigencias o divida la autorización.'))
    policy=dict(rows[0]);validate_policy(policy)
    policy['calculator_version']=VERSION
    return policy
