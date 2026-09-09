import frappe
from frappe.utils import cint

from .service import REQUEST, _save, audit, settings
from .rules import money


def validate_settings(doc, method=None):
    companies, methods = set(), set()
    for row in doc.get('dieta_companies') or []:
        if row.company in companies:
            frappe.throw('Configure una sola fila de Dietas por compañía.')
        companies.add(row.company)
        if row.enabled:
            try:
                money(row.default_amount)
            except ValueError as exc:
                frappe.throw(str(exc))
        if row.generate_journal_entry:
            from .accounting import _validate_account
            currency = frappe.db.get_value('Company', row.company, 'default_currency')
            _validate_account(row.expense_account, row.company, 'expense', currency)
    for row in doc.get('dieta_payment_methods') or []:
        key = (row.company, row.mode_of_payment)
        if key in methods or row.company not in companies:
            frappe.throw('Revise la compañía y los métodos de pago duplicados de Dietas.')
        methods.add(key)
        cfg = next(c for c in doc.dieta_companies if c.company == row.company)
        if cfg.generate_journal_entry:
            from .accounting import _validate_account
            _validate_account(row.payment_account, row.company, 'payment',
                              frappe.db.get_value('Company', row.company, 'default_currency'))
    if any(c.enabled and not any(m.company == c.company for m in doc.get('dieta_payment_methods') or []) for c in doc.get('dieta_companies') or []):
        frappe.throw('Configure al menos un método de pago por compañía habilitada.')


def validate_work_call(doc, method=None):
    if any(cint(row.get('allows_dieta')) for row in doc.dates) and doc.docstatus == 0:
        settings(doc.company)
    before = doc.get_doc_before_save()
    if before and before.docstatus == 1:
        old = {r.name: cint(r.get('allows_dieta')) for r in before.dates}
        if any(old.get(r.name) != cint(r.get('allows_dieta')) for r in doc.dates):
            frappe.throw('Permite dieta se define antes de autorizar la convocatoria.')


def lock_authorization(doc, method=None):
    # Match payout lock order. Also used before cancellation and reconciliation
    # saves to serialize source validity with payout confirmation.
    if doc.overtime_work_call:
        frappe.db.get_value('Overtime Work Call', doc.overtime_work_call, 'name', for_update=True)
    frappe.db.get_value('Employee', doc.employee, 'name', for_update=True)


def authorization_cancelled(doc, method=None):
    if not frappe.db.exists('DocType', REQUEST):
        return
    lock_authorization(doc)
    for name in frappe.get_all(REQUEST, filters={'authorization': doc.name}, pluck='name'):
        req = frappe.get_doc(REQUEST, name)
        if req.payment_status == 'Paid':
            req.review_required = 1
            req.review_reason = 'Autorización cancelada después del pago.'
        else:
            req.approval_status = 'Cancelled'
        audit(req, 'authorization_cancelled', authorization=doc.name)
        _save(req, historical=True)


def flag_attendance_review(doc, method=None):
    if not frappe.db.exists('DocType', REQUEST):
        return
    if doc.get('reconciliation_status') not in ('Absent', 'Partial', 'Check-in Issue', 'Overrun'):
        return
    for name in frappe.get_all(REQUEST, filters={'authorization': doc.name, 'payment_status': 'Paid'}, pluck='name'):
        req = frappe.get_doc(REQUEST, name)
        reason = 'Revisar asistencia: ' + doc.reconciliation_status
        if req.review_reason == reason:
            continue
        req.review_required = 1
        req.review_reason = reason
        audit(req, 'attendance_review', reason)
        _save(req, historical=True)


def lock_work_call(doc, method=None):
    frappe.db.get_value('Overtime Work Call', doc.name, 'name', for_update=True)
    for name in sorted({row.employee for row in doc.employees}):
        frappe.db.get_value('Employee', name, 'name', for_update=True)
