"""Select immutable policy revisions and preserve reconciled source versions."""
from datetime import timedelta
import frappe
from frappe import _
from frappe.utils import get_datetime,getdate
from powerpro.controllers.overtime import _reconciliation_rows
from powerpro.payroll_rules.overtime_pay_policy import FIELDS,VERSION,validate_policy


def policy_rows(company, start, last, *, for_update=False):
    rows=_reconciliation_rows('Overtime Pay Policy',for_update=for_update,
        filters=[['company','=',company],['docstatus','=',1],['valid_from','<=',last],['valid_until','>=',start]],
        fields=list(FIELDS)+['supersedes'],order_by='creation asc, name asc',limit=1001)
    if len(rows)>1000:frappe.throw(_('Demasiadas versiones de reglas para esta vigencia.'))
    return rows


def active_revisions(rows):
    replaced={r.get('supersedes') for r in rows if r.get('supersedes')}
    return [r for r in rows if r.name not in replaced]


def _saved_policy(doc, *, for_update=False):
    # Read the persisted source, never a policy name supplied in a client snapshot.
    dt=doc.get('doctype');name=doc.get('name')
    if dt not in {'Overtime Authorization','Retroactive Overtime Adjustment','Ordinary Night Settlement'} or not name:
        return None
    rows=_reconciliation_rows(dt,for_update=for_update,filters={'name':name,'docstatus':1},
        fields=['evidence_snapshot'],limit=1)
    if not rows:return None
    saved=frappe.parse_json(rows[0].evidence_snapshot or '{}')
    inputs=saved.get('input') or {}
    policy=inputs.get('pay_policy') or inputs.get('policy') or {}
    if not saved.get('input_hash') or not policy.get('name'):return None
    rows=_reconciliation_rows('Overtime Pay Policy',for_update=for_update,
        filters={'name':policy['name'],'docstatus':1},fields=list(FIELDS),limit=1)
    if not rows:frappe.throw(_('La versión de reglas de esta conciliación ya no está aprobada.'))
    return rows[0]


def get_effective_policy(doc,*,for_update=False):
    start=getdate(doc.authorization_start)
    last=(get_datetime(doc.authorization_end)-timedelta(microseconds=1)).date()
    saved=_saved_policy(doc,for_update=for_update)
    rows=[saved] if saved else active_revisions(policy_rows(doc.company,start,last,for_update=for_update))
    if not rows:return None
    if len(rows)!=1 or rows[0].company!=doc.company or getdate(rows[0].valid_from)>start or getdate(rows[0].valid_until)<last:
        frappe.throw(_('La ventana debe estar cubierta por una sola política aprobada. Revise vigencias o divida la autorización.'))
    policy={k:rows[0].get(k) for k in FIELDS};validate_policy(policy)
    policy['calculator_version']=VERSION
    return policy
