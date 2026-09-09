"""Batch-only accounting generator. No public arbitrary-account or posting API."""
import frappe
from frappe.utils import now_datetime

from . import permissions as access
from .service import BATCH, REQUEST, _save, audit, atomic


def queue_journal(batch_name):
    frappe.db.after_commit.add(lambda: _enqueue(batch_name))


def _enqueue(batch_name):
    try:
        frappe.enqueue('powerpro.dietas.accounting.generate_journal', batch_name=batch_name,
                       job_name='dieta-je-' + batch_name)
    except Exception:
        # The payout has already committed. A queue outage is an accounting issue.
        frappe.db.set_value(BATCH, batch_name, {'accounting_status': 'Error',
            'accounting_error': 'No se pudo iniciar la contabilidad. Reintente desde Ver pagos.'})
        frappe.db.commit()
        frappe.log_error(title='Dieta accounting queue failed')


def _validate_account(name, company, kind, currency):
    if not name:
        frappe.throw('Falta configurar la cuenta de dietas o de pago.')
    account = frappe.get_doc('Account', name)
    if account.is_group:
        frappe.throw(f'La cuenta {name} es un grupo. Seleccione una cuenta de movimiento (sin "Es un grupo").')
    if account.company != company or account.disabled:
        frappe.throw('La cuenta debe estar activa, ser de movimiento y pertenecer a la compañía.')
    if kind == 'expense' and account.root_type != 'Expense':
        frappe.throw('Configure una cuenta de gastos para las dietas.')
    if kind == 'payment' and account.account_type not in ('Cash', 'Bank'):
        frappe.throw('Configure una cuenta de caja o banco para el pago.')
    if account.account_currency and account.account_currency != currency:
        frappe.throw('Las dietas requieren cuentas en la moneda de la compañía.')


def _validate_cost_center(name, company):
    if not name:
        frappe.throw('Configure un centro de costo para las dietas.')
    center = frappe.get_doc('Cost Center', name)
    if center.is_group:
        frappe.throw(f'El centro de costo {name} es un grupo. Seleccione un centro de costo de movimiento.')
    if center.company != company:
        frappe.throw('El centro de costo debe pertenecer a la compañía de la dieta.')


def generate_journal(batch_name):
    """Internal background entry point; serialized by the durable batch row."""
    frappe.db.get_value(BATCH, batch_name, 'name', for_update=True)
    batch = frappe.get_doc(BATCH, batch_name, for_update=True)
    if batch.status != 'Confirmed' or not batch.generate_journal_entry:
        return
    if batch.journal_entry:
        if frappe.db.exists('Journal Entry', batch.journal_entry):
            status = frappe.db.get_value('Journal Entry', batch.journal_entry, 'docstatus')
            batch.accounting_status = {0: 'Draft', 1: 'Posted', 2: 'Cancelled'}[status]
            _save(batch, historical=True)
        return
    # A draft and its batch link commit together. Failed generation rolls back only
    # this savepoint, leaving the previously committed payout intact.
    frappe.db.savepoint('dieta_accounting')
    try:
        _validate_account(batch.expense_account, batch.company, 'expense', batch.currency)
        _validate_account(batch.payment_account, batch.company, 'payment', batch.currency)
        _validate_cost_center(batch.cost_center, batch.company)
        je = frappe.new_doc('Journal Entry')
        je.update(dict(voucher_type='Journal Entry', company=batch.company,
                       posting_date=batch.payment_date, cheque_no=batch.reference,
                       cheque_date=batch.payment_date if batch.reference else None,
                       user_remark='Pago de dietas: ' + batch.name))
        # One debit per worker keeps employee/request detail in the draft without
        # using an unrelated payable/receivable party or settlement reference.
        for row in batch.rows:
            je.append('accounts', dict(account=batch.expense_account,
                debit_in_account_currency=row.amount, cost_center=batch.cost_center,
                user_remark=f'{row.employee_name} / {row.request}'))
        je.append('accounts', dict(account=batch.payment_account, credit_in_account_currency=batch.total))
        je.insert(ignore_permissions=True)
        batch.journal_entry = je.name
        batch.accounting_status = 'Draft'
        batch.accounting_error = ''
        audit(batch, 'journal_draft', journal_entry=je.name)
        _save(batch, historical=True)
    except Exception:
        frappe.db.rollback(save_point='dieta_accounting')
        batch.reload()
        batch.accounting_status = 'Error'
        batch.accounting_error = 'No se pudo generar el asiento. Finanzas debe revisar las cuentas y dimensiones configuradas.'
        _save(batch, historical=True)
        frappe.log_error(title='Dieta Journal Entry failed')


@frappe.whitelist(methods=['POST'])
def retry_accounting(batch_name):
    batch = frappe.get_doc(BATCH, batch_name, for_update=True)
    if not access.batch_permission(batch):
        frappe.throw('No tiene permiso sobre este lote.', frappe.PermissionError)
    if batch.status != 'Confirmed' or not batch.generate_journal_entry:
        frappe.throw('Este lote no tiene contabilidad habilitada.')
    if batch.journal_entry:
        frappe.throw('Este lote ya tiene un asiento. Finanzas debe resolverlo antes de generar otro.')
    queue_journal(batch.name)
    return {'queued': True}


def journal_status(doc, method=None):
    if not frappe.db.exists('DocType', BATCH):
        return
    name = frappe.db.get_value(BATCH, {'journal_entry': doc.name}, 'name')
    if not name:
        return
    frappe.db.get_value(BATCH, name, 'name', for_update=True)
    batch = frappe.get_doc(BATCH, name, for_update=True)
    batch.accounting_status = {0: 'Draft', 1: 'Posted', 2: 'Cancelled'}[doc.docstatus]
    audit(batch, 'journal_status', journal_entry=doc.name, status=batch.accounting_status)
    _save(batch, historical=True)


def protect_journal(doc, method=None):
    if not frappe.db.exists('DocType', BATCH):
        return
    if frappe.db.exists(BATCH, {'journal_entry': doc.name}):
        frappe.throw('Este asiento está vinculado a un pago de dietas. Cancele o corrija mediante Finanzas; no elimine el historial.')


@frappe.whitelist(methods=['POST'])
@atomic
def reverse_erroneous_payout(batch_name, reason):
    """Clerical correction only: no money transfer/refund is inferred."""
    if 'HR Manager' not in frappe.get_roles() or not str(reason or '').strip():
        frappe.throw('La corrección requiere HR Manager y un motivo.', frappe.PermissionError)
    initial = frappe.get_doc(BATCH, batch_name)
    frappe.db.get_value('Overtime Work Call', initial.overtime_work_call, 'name', for_update=True)
    for row in sorted(initial.rows, key=lambda r: r.employee):
        frappe.db.get_value('Employee', row.employee, 'name', for_update=True)
    frappe.db.get_value(BATCH, batch_name, 'name', for_update=True)
    batch = frappe.get_doc(BATCH, batch_name, for_update=True)
    if not access.batch_permission(batch):
        frappe.throw('No tiene permiso sobre este lote.', frappe.PermissionError)
    if batch.status == 'Reversed':
        return {'reversed': batch.name}
    if batch.journal_entry and frappe.db.get_value('Journal Entry', batch.journal_entry, 'docstatus') != 2:
        frappe.throw('Finanzas debe resolver y cancelar el asiento antes de corregir el pago.')
    for row in batch.rows:
        req = frappe.get_doc(REQUEST, row.request, for_update=True)
        if req.payout_batch != batch.name or req.payment_status != 'Paid':
            frappe.throw('El pago de la solicitud cambió; revise el historial.')
        audit(req, 'reverse_erroneous_payment', reason, batch=batch.name, amount=row.amount)
        source_active = frappe.db.get_value('Overtime Authorization', req.authorization, 'docstatus') == 1
        req.update(dict(payment_status='Unpaid', approval_status='Pending' if source_active else 'Cancelled', payout_batch=None,
                        paid_by=None, paid_on=None, approved_by=None, approved_on=None,
                        review_required=1, review_reason='Pago registrado por error: ' + reason))
        _save(req, historical=True)
    batch.status = 'Reversed'
    audit(batch, 'reverse_erroneous_payment', reason, at_review=str(now_datetime()))
    _save(batch, historical=True)
    return {'reversed': batch.name}


def validate_managed_journal(doc, method=None):
    if not frappe.db.exists('DocType', BATCH):
        return
    name = frappe.db.get_value(BATCH, {'journal_entry': doc.name}, 'name')
    if not name:
        return
    batch = frappe.get_doc(BATCH, name, for_update=True)
    if batch.status != 'Confirmed':
        frappe.throw('El pago de dieta fue corregido; no puede contabilizarse.')
    debits = sum(float(r.debit_in_account_currency or 0) for r in doc.accounts)
    credits = sum(float(r.credit_in_account_currency or 0) for r in doc.accounts)
    if doc.company != batch.company or abs(debits - batch.total) > 0.001 or abs(credits - batch.total) > 0.001:
        frappe.throw('El asiento debe conservar la compañía y el total del pago de dietas.')
