"""Atomic holiday cash plus weekly-rest credit, with independent cash status."""
import json
import frappe
from frappe import _
from powerpro.controllers.overtime_source import evidence_enabled
from powerpro.payroll_rules.overtime_combined_day import combined_hours, hybrid_cash_calculation


def is_candidate(doc):
    snapshot=frappe.parse_json(doc.get('evidence_snapshot') or '{}')
    return bool(evidence_enabled(doc) and doc.planned_settlement=='Compensatory Rest'
                and combined_hours(snapshot.get('calculation')))


def reconciliation(doc):
    from powerpro.controllers.retroactive_evidence import as_reconciliation
    snapshot=frappe.parse_json(doc.get('evidence_snapshot') or '{}')
    result=as_reconciliation(doc,snapshot)
    hybrid_cash_calculation(result.get('pay_policy'),result)
    election=result.get('settlement_election') or {}
    if election.get('choice')!='Compensatory Rest' or not election.get('settlement_payroll_date'):
        frappe.throw(_('Confirme la elección del empleado y la fecha del pago del feriado.'))
    doc.settlement_payroll_date=election['settlement_payroll_date']
    return result


def preview_hybrid(doc, *, settings=None, bank_state=None, evidence=None):
    from powerpro.controllers.overtime_cash_settlement import build_cash_settlement,_validate_cash_settlement
    from powerpro.controllers.overtime_compensatory_settlement import build_compensatory_preview
    if evidence is not None:
        doc=frappe.get_doc(doc.as_dict())
        doc.evidence_snapshot=json.dumps(evidence,default=str)
    cash=build_cash_settlement(doc,reconciliation(doc));_validate_cash_settlement(cash)
    credit=build_compensatory_preview(doc,settings=settings,bank_state=bank_state)
    return {**credit,'holiday_cash':cash,'holiday_cash_amount':cash['total_amount']}


def create_hybrid(doc):
    from powerpro.controllers.overtime_settlement import _credit_only_and_record
    from powerpro.controllers.overtime_cash_settlement import create_cash_settlement_for_source
    if doc.get('holiday_cash_status') or doc.settlement_status in {'Created','Payroll Submitted','Paid','Credited','Cancelled'}:
        frappe.throw(_('Esta obligación combinada ya tiene una liquidación.'))
    preview_hybrid(doc)
    point='hybrid_'+frappe.generate_hash(length=10)
    frappe.db.savepoint(point)
    try:
        cash,cash_values=create_cash_settlement_for_source(doc,reconciliation(doc))
        credit=_credit_only_and_record(doc)
        doc.reload()
        rest_breakdown=frappe.parse_json(doc.settlement_breakdown)
        values={**cash_values,'settlement_status':'Credited','settlement_method':'Compensatory Rest',
                'holiday_cash_status':'Created',
                'settlement_breakdown':json.dumps({**rest_breakdown,'holiday_cash':cash},default=str,ensure_ascii=False)}
        # Forward cash references remain typed as Additional Salary; credit/allocation
        # retain their existing explicit Link fields and immutable credit ledger.
        doc.db_set(values)
        return {**credit,'holiday_cash':cash,'holiday_cash_amount':cash['total_amount']}
    except Exception:
        frappe.db.rollback(save_point=point)
        doc.reload()
        raise


def cancel_hybrid(doc):
    from powerpro.controllers.overtime_cash_settlement import before_cancel_adjustment,cancel_cash_settlement
    from powerpro.controllers.overtime_compensatory_settlement import reverse_compensatory_credit
    point='cancel_hybrid_'+frappe.generate_hash(length=10)
    frappe.db.savepoint(point)
    try:
        before_cancel_adjustment(doc)
        reverse_compensatory_credit(doc)
        cancel_cash_settlement(doc)
        doc.db_set({'settlement_status':'Cancelled','holiday_cash_status':'Cancelled'})
    except Exception:
        frappe.db.rollback(save_point=point)
        raise


def reverse_hybrid(doc,event):
    """Use the same financial guards for audited evidence correction as cancellation."""
    from powerpro.controllers.overtime_cash_settlement import before_cancel_adjustment,_get_linked_additional_salaries
    from powerpro.controllers.overtime_compensatory_settlement import reverse_compensatory_credit
    point='reverse_hybrid_'+frappe.generate_hash(length=10)
    frappe.db.savepoint(point)
    previous=frappe.flags.get('overtime_evidence_reversal')
    try:
        before_cancel_adjustment(doc)
        frappe.db.set_value(doc.doctype,doc.name,'compensatory_credit',None,update_modified=False)
        reverse_compensatory_credit(doc,reason='Revisión '+event.name+': '+event.reason)
        frappe.flags.overtime_evidence_reversal=(doc.doctype,doc.name)
        for name in _get_linked_additional_salaries(doc,docstatus=1,for_update=True):
            salary=frappe.get_doc('Additional Salary',name,for_update=True)
            salary.flags.ignore_permissions=True;salary.cancel()
        doc.db_set('holiday_cash_status','Cancelled')
    except Exception:
        frappe.db.rollback(save_point=point)
        raise
    finally:
        frappe.flags.overtime_evidence_reversal=previous
