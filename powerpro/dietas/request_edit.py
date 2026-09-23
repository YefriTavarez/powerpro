"""Controlled edits of saved requests; generic document writes stay forbidden."""
import frappe

from . import permissions as access
from . import service
from .rules import money, override_required


def can_edit(doc, emp):
    return bool(doc.docstatus == 0 and doc.approval_status == 'Pending'
                and doc.payment_status == 'Unpaid' and not doc.payout_batch
                and emp.status == 'Active' and emp.company == doc.company
                and (access.can_manage(emp) or (
                    doc.initiated_by == frappe.session.user
                    and access.can_create_for_employee(emp))))


@frappe.whitelist()
def get_context(request):
    doc = frappe.get_doc(access.REQUEST, request)
    if not access.can_read_request(doc):
        frappe.throw('No tiene permiso sobre esta solicitud de dieta.', frappe.PermissionError)
    emp = access.employee(doc.employee)
    return dict(request=doc.name, modified=str(doc.modified), amount=doc.amount,
                notes=doc.notes or '', currency=doc.currency, can_edit=can_edit(doc, emp),
                expense_approver=emp.get('expense_approver'),
                work_call=doc.overtime_work_call,
                approval_status=doc.approval_status, payment_status=doc.payment_status)


@frappe.whitelist(methods=['POST'])
@service.atomic
def update_request(request, modified, amount, notes=''):
    # Use stored identities, not client-supplied employee/company/status fields.
    # Match the payout lock order: Work Call -> employee -> settings -> auth -> request.
    initial = frappe.get_doc(access.REQUEST, request)
    if not access.can_read_request(initial):
        frappe.throw('No tiene permiso sobre esta solicitud de dieta.', frappe.PermissionError)
    call = service._call(initial.overtime_work_call, lock=True) if initial.overtime_work_call else None
    emp = access.employee(initial.employee, lock=True)
    cfg = service.settings(initial.company, lock=True)
    auth = (frappe.get_doc('Overtime Authorization', initial.authorization, for_update=True)
            if initial.authorization else None)
    doc = frappe.get_doc(access.REQUEST, request, for_update=True)
    if not can_edit(doc, emp):
        frappe.throw('Solo el solicitante autorizado o el aprobador puede editar una dieta pendiente e impagada.',
                     frappe.PermissionError)
    if not modified or str(doc.modified) != str(modified) or any(
            doc.get(field) != initial.get(field)
            for field in ('employee', 'company', 'overtime_work_call', 'authorization')):
        frappe.throw('La solicitud cambió. Recargue el documento antes de editar.')
    if call:
        if call.company != doc.company or not any(row.employee == emp.name for row in call.employees):
            frappe.throw('El empleado ya no pertenece a esta convocatoria.')
        service._eligible_date(call, doc.work_date)
    if auth and (auth.docstatus != 1 or auth.employee != doc.employee
                 or auth.company != doc.company
                 or service.getdate(auth.work_date) != service.getdate(doc.work_date)
                 or (call and auth.overtime_work_call != call.name)):
        frappe.throw('La autorización ya no está vigente o no corresponde a esta solicitud.')
    if doc.currency != cfg.currency:
        frappe.throw('La moneda de la empresa cambió. Revise la solicitud antes de continuar.')
    amount = service._rule(money, amount)
    notes = str(notes or '').strip()
    # Retain the request's historical default, even if company settings changed.
    if override_required(doc.default_amount, amount) and not notes:
        frappe.throw('Indique en Notas el motivo del cambio de monto.')
    if amount == doc.amount and notes == (doc.notes or ''):
        return dict(request=doc.name, modified=str(doc.modified))
    service.audit(doc, 'edit', notes, previous_amount=doc.amount, amount=amount,
                  previous_notes=doc.notes or '')
    doc.amount, doc.notes = amount, notes
    service._save(doc)
    return dict(request=doc.name, modified=str(doc.modified))
