"""Select immutable policy revisions and preserve reconciled source versions."""
from datetime import timedelta
import frappe
from frappe import _
from frappe.utils import get_datetime,getdate
from powerpro.controllers.overtime import _reconciliation_rows
from powerpro.payroll_rules.overtime_pay_policy import FIELDS
from powerpro.payroll_rules.overtime_combined_day import FIELD, REST_FIELD
from powerpro.payroll_rules.overtime_policy_coverage import compose_coverage, policy_names


def policy_rows(company, start, last, *, for_update=False):
    rows=_reconciliation_rows('Overtime Pay Policy',for_update=for_update,
        filters=[['company','=',company],['docstatus','=',1],['valid_from','<=',last],['valid_until','>=',start]],
        fields=list(FIELDS)+['supersedes',FIELD,REST_FIELD],order_by='creation asc, name asc',limit=1001)
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
    names=policy_names(policy)
    if not names or len(names)>1000 or len(names)!=len(set(names)) or names[0]!=policy['name']:
        frappe.throw(_('La cadena de reglas guardada no es válida. Revise la conciliación.'))
    rows=_reconciliation_rows('Overtime Pay Policy',for_update=for_update,
        filters={'name':['in',names],'docstatus':1},fields=list(FIELDS)+[FIELD,REST_FIELD],limit=len(names))
    if {r.name for r in rows}!=set(names):
        frappe.throw(_('La versión de reglas de esta conciliación ya no está aprobada.'))
    return rows


def get_effective_policy(doc,*,for_update=False):
    start=getdate(doc.authorization_start)
    last=(get_datetime(doc.authorization_end)-timedelta(microseconds=1)).date()
    saved=_saved_policy(doc,for_update=for_update)
    rows=saved if saved else active_revisions(policy_rows(doc.company,start,last,for_update=for_update))
    if not rows:return None
    try:return compose_coverage(rows,doc.company,start,last)
    except ValueError as exc:frappe.throw(_(str(exc)))
