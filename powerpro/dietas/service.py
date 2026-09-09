"""Dieta APIs. Server-derived identities, scoped access, atomic payout batches."""
import json
import uuid
from functools import wraps

import frappe
from frappe.utils import cint, getdate, now_datetime

from . import permissions as access
from .rules import check_payable, check_transition, day_key, digest, money, override_required

REQUEST = access.REQUEST
BATCH = access.BATCH


def atomic(fn):
    """Also roll back when invoked by another Python caller that catches errors."""
    @wraps(fn)
    def wrapped(*args, **kwargs):
        point = 'dieta_' + uuid.uuid4().hex
        frappe.db.savepoint(point)
        try:
            return fn(*args, **kwargs)
        except Exception:
            frappe.db.rollback(save_point=point)
            raise
    return wrapped


def _json(value):
    return frappe.parse_json(value) if isinstance(value, str) else value


def _fail(message):
    frappe.throw(message)


def _rule(fn, *args):
    try:
        return fn(*args)
    except ValueError as exc:
        _fail(str(exc))


def _save(doc, historical=False):
    doc.flags.dieta_service = True
    if historical:
        doc.flags.ignore_links = True
    doc.save(ignore_permissions=True)
    return doc


def audit(doc, action, reason='', **details):
    events = json.loads(doc.audit_log or '[]')
    events.append(dict(action=action, reason=reason, user=frappe.session.user,
                       at=str(now_datetime()), **details))
    doc.audit_log = json.dumps(events, ensure_ascii=False, default=str)


def settings(company, lock=False, require_enabled=True):
    rows = frappe.db.get_values('Dieta Company Settings', {'parent': 'IGC Settings', 'company': company}, 'name', pluck=True, for_update=lock)
    if len(rows) != 1:
        _fail('Configure una fila de Dietas para esta compañía en IGC Settings.')
    if lock:
        frappe.db.get_value('Dieta Company Settings', rows[0], 'name', for_update=True)
    cfg = frappe.get_doc('Dieta Company Settings', rows[0], for_update=lock)
    if require_enabled and not cint(cfg.enabled):
        _fail('Las dietas están deshabilitadas para esta compañía.')
    cfg.default_amount = _rule(money, cfg.default_amount)
    cfg.currency = frappe.db.get_value('Company', company, 'default_currency')
    cfg.methods = frappe.db.get_values('Dieta Payment Method',
        {'parent': 'IGC Settings', 'company': company}, ['name', 'mode_of_payment', 'payment_account', 'modified'], as_dict=True, for_update=lock)
    return cfg


def _call(name, lock=False, active=True, check_read=True):
    if lock:
        frappe.db.get_value('Overtime Work Call', name, 'name', for_update=True)
    call = frappe.get_doc('Overtime Work Call', name, for_update=lock)
    if check_read:
        call.check_permission('read')
    if active and call.docstatus != 1:
        _fail('La convocatoria debe estar autorizada y vigente.')
    return call


def _eligible_date(call, date):
    date = getdate(date)
    if not any(getdate(row.work_date) == date and cint(row.get('allows_dieta')) for row in call.dates):
        _fail('La fecha no permite dieta en esta convocatoria.')
    return date


def _employee(name, manage=True, lock=False):
    emp = access.employee(name, lock=lock)
    allowed = access.can_manage(emp) if manage else (
        frappe.session.user != 'Guest' and emp.user_id == frappe.session.user and access.in_scope(emp))
    if not allowed:
        frappe.throw('No tiene permiso sobre la dieta de este empleado.', frappe.PermissionError)
    return emp


def _authorization(call, emp, date, lock=False):
    if emp.status != 'Active' or emp.company != call.company or not any(r.employee == emp.name for r in call.employees):
        _fail('El empleado no está activo o no pertenece a esta convocatoria.')
    rows = frappe.db.get_values('Overtime Authorization', {
        'overtime_work_call': call.name, 'employee': emp.name, 'work_date': date, 'docstatus': 1}, 'name', pluck=True, for_update=lock)
    if len(rows) != 1:
        _fail('No se encontró una autorización individual vigente para la fecha.')
    if lock:
        frappe.db.get_value('Overtime Authorization', rows[0], 'name', for_update=True)
    auth = frappe.get_doc('Overtime Authorization', rows[0], for_update=lock)
    if auth.docstatus != 1:
        _fail('La autorización cambió; actualice la convocatoria.')
    return auth


def _request(company, employee, date, lock=False):
    key = day_key(company, employee, date)
    exists = frappe.db.get_value(REQUEST, key, 'name', for_update=lock)
    return frappe.get_doc(REQUEST, key, for_update=lock) if exists else None


def _version(call, auth, emp, cfg, req):
    return digest([call.modified, auth.modified, auth.docstatus, emp.modified,
                   cfg.as_dict(), req.as_dict() if req else None])


def _row(call, auth, emp, cfg, req):
    amount = req.amount if req else cfg.default_amount
    return dict(employee=emp.name, employee_name=emp.employee_name,
        authorization=auth.name, start=str(auth.authorization_start), end=str(auth.authorization_end),
        request=req.name if req else None, amount=amount,
        approval_status=req.approval_status if req else 'None',
        payment_status=req.payment_status if req else 'Unpaid',
        review_required=req.review_required if req else 0,
        review_reason=req.review_reason if req else '',
        source_work_call=req.overtime_work_call if req else call.name,
        notes=req.notes if req else '', audit=json.loads(req.audit_log or '[]') if req else [],
        version=_version(call, auth, emp, cfg, req))


@frappe.whitelist()
def work_call_context(work_call, work_date=None):
    call = _call(work_call, active=False)
    if not frappe.db.exists('DocType', REQUEST):
        return {'enabled': False}
    names = frappe.get_all('Dieta Company Settings', filters={'parent': 'IGC Settings', 'company': call.company, 'enabled': 1}, pluck='name')
    configured = frappe.db.exists('Dieta Company Settings', {'parent': 'IGC Settings', 'company': call.company})
    if not configured:
        return {'enabled': False}
    cfg = settings(call.company, require_enabled=False)
    dates = [str(getdate(r.work_date)) for r in call.dates if cint(r.get('allows_dieta'))]
    visible = [r.employee for r in call.employees if access.can_manage(access.employee(r.employee))]
    if not visible:
        return {'enabled': False}
    requests = frappe.get_all(REQUEST, filters={'overtime_work_call': call.name, 'employee': ['in', visible]},
        fields=['approval_status', 'payment_status', 'amount'])
    batches = _history(call)
    summary = dict(pending=sum(r.approval_status == 'Pending' and r.payment_status != 'Paid' for r in requests),
        approved_unpaid=sum(r.amount for r in requests if r.approval_status == 'Approved' and r.payment_status != 'Paid'),
        paid=sum(b['total'] for b in batches if b['status'] == 'Confirmed'),
        accounting_attention=sum(b['accounting_status'] in ('Pending', 'Error', 'Cancelled') for b in batches if b['status'] == 'Confirmed'))
    result = dict(enabled=True, work_call=call.name, dates=dates, currency=cfg.currency, default_amount=cfg.default_amount,
                  methods=[r.mode_of_payment for r in cfg.methods], summary=summary, rows=[], active=call.docstatus == 1 and bool(cint(cfg.enabled)))
    if work_date and call.docstatus == 1 and cint(cfg.enabled):
        date = _eligible_date(call, work_date)
        for name in visible:
            emp = access.employee(name)
            if emp.status != 'Active':
                continue
            auths = frappe.get_all('Overtime Authorization', filters={'overtime_work_call': call.name,
                'employee': name, 'work_date': date, 'docstatus': 1}, pluck='name')
            if len(auths) != 1:
                continue
            auth = frappe.get_doc('Overtime Authorization', auths[0])
            result['rows'].append(_row(call, auth, emp, cfg, _request(call.company, name, date)))
    return result


def _selections(rows):
    rows = _json(rows)
    if not isinstance(rows, list) or not rows or len(rows) > 1000:
        _fail('Seleccione entre 1 y 1000 empleados.')
    if any(not isinstance(r, dict) or not r.get('employee') or not r.get('version') for r in rows):
        _fail('Actualice los empleados antes de continuar.')
    if len({r['employee'] for r in rows}) != len(rows):
        _fail('Hay empleados duplicados en la selección.')
    return sorted(rows, key=lambda r: r['employee'])


def _prepare(work_call, work_date, rows, lock=False, payable=True):
    rows = _selections(rows)
    call = _call(work_call, lock=lock)
    date = _eligible_date(call, work_date)
    if lock:
        # Stable employee locks also serialize requests from different work calls.
        for row in rows:
            frappe.db.get_value('Employee', row['employee'], 'name', for_update=True)
    cfg = settings(call.company, lock=lock)
    prepared = []
    for row in rows:
        emp = _employee(row['employee'], lock=lock)
        auth = _authorization(call, emp, date, lock=lock)
        req = _request(call.company, emp.name, date, lock=lock)
        if row['version'] != _version(call, auth, emp, cfg, req):
            _fail('Los datos cambiaron; actualice los empleados y revise los montos.')
        if payable:
            _rule(check_payable, req)
            if req and req.overtime_work_call != call.name:
                _fail('Esta dieta pertenece a otra convocatoria; gestiónela desde su origen.')
        amount = _rule(money, row.get('amount', req.amount if req else cfg.default_amount))
        original = req.amount if req else cfg.default_amount
        reason = str(row.get('reason') or '').strip()
        if override_required(original, amount) and not reason:
            _fail('Indique el motivo del cambio de monto.')
        prepared.append(dict(emp=emp, auth=auth, req=req, amount=amount, original=original, reason=reason))
    return call, date, cfg, prepared


def _payment(cfg, payment_date, mode_of_payment, reference, evidence):
    if not payment_date:
        _fail('Indique la fecha real del pago.')
    date = getdate(payment_date)
    if date > getdate():
        _fail('No puede confirmar un pago realizado en una fecha futura.')
    methods = [r for r in cfg.methods if r.mode_of_payment == mode_of_payment]
    if len(methods) != 1:
        _fail('Seleccione un método de pago configurado para esta compañía.')
    if evidence:
        files = frappe.get_all('File', filters={'file_url': evidence}, pluck='name')
        if not files or not any(frappe.has_permission('File', 'read', doc=frappe.get_doc('File', n)) for n in files):
            frappe.throw('No tiene acceso al comprobante.', frappe.PermissionError)
    return dict(payment_date=str(date), mode_of_payment=mode_of_payment,
                payment_account=methods[0].payment_account, reference=str(reference or ''), evidence=evidence or '')


def _preview(call, date, cfg, prepared, payment):
    rows = [dict(employee=p['emp'].name, employee_name=p['emp'].employee_name,
        amount=p['amount'], reason=p['reason'], version=_version(call, p['auth'], p['emp'], cfg, p['req'])) for p in prepared]
    result = dict(work_call=call.name, work_date=str(date), company=call.company, currency=cfg.currency,
        rows=rows, total=round(sum(r['amount'] for r in rows), 2), payment=payment)
    result['token'] = digest(result)
    return result


@frappe.whitelist()
def preview_payout(work_call, work_date, rows, payment_date, mode_of_payment, reference=None, evidence=None):
    call, date, cfg, prepared = _prepare(work_call, work_date, rows)
    payment = _payment(cfg, payment_date, mode_of_payment, reference, evidence)
    return _preview(call, date, cfg, prepared, payment)


def _new_request(call, date, cfg, p, origin):
    req = frappe.new_doc(REQUEST)
    req.update(dict(day_key=day_key(call.company, p['emp'].name, date), employee=p['emp'].name,
        employee_name=p['emp'].employee_name, company=call.company, work_date=date,
        overtime_work_call=call.name, authorization=p['auth'].name, currency=cfg.currency,
        default_amount=cfg.default_amount, amount=p['amount'], origin=origin,
        initiated_by=frappe.session.user, approval_status='Pending', payment_status='Unpaid'))
    audit(req, 'request', origin=origin, default_amount=cfg.default_amount, amount=p['amount'])
    return req


@frappe.whitelist(methods=['POST'])
@atomic
def confirm_payout(work_call, work_date, rows, payment_date, mode_of_payment, token,
                   idempotency_key, reference=None, evidence=None):
    try:
        uuid.UUID(idempotency_key)
    except (ValueError, TypeError, AttributeError):
        _fail('Identificador de pago inválido.')
    payload = digest([work_call, str(work_date), _selections(rows), payment_date, mode_of_payment, token, reference, evidence])
    # Work-call lock makes retries wait for the first commit, before checking the key.
    call = _call(work_call, lock=True, active=False)
    existing = frappe.db.get_value(BATCH, {'idempotency_key': idempotency_key}, 'name', for_update=True)
    if existing:
        batch = frappe.get_doc(BATCH, existing, for_update=True)
        if batch.payload_hash != payload or not access.batch_permission(batch):
            _fail('El identificador corresponde a otro pago o selección.')
        return _batch_result(batch)
    call, date, cfg, prepared = _prepare(work_call, work_date, rows, lock=True)
    payment = _payment(cfg, payment_date, mode_of_payment, reference, evidence)
    preview = _preview(call, date, cfg, prepared, payment)
    if token != preview['token']:
        _fail('La vista previa cambió. Revise y confirme nuevamente.')
    batch = frappe.new_doc(BATCH)
    batch.update(dict(idempotency_key=idempotency_key, payload_hash=payload, company=call.company,
        overtime_work_call=call.name, work_date=date, currency=cfg.currency,
        **payment, total=preview['total'], paid_by=frappe.session.user, paid_on=now_datetime(),
        status='Confirmed', generate_journal_entry=cint(cfg.generate_journal_entry),
        expense_account=cfg.expense_account, cost_center=cfg.cost_center,
        accounting_status='Pending' if cfg.generate_journal_entry else 'Disabled'))
    requests = []
    for p in prepared:
        req = p['req'] or _new_request(call, date, cfg, p, 'Manager')
        audit(req, 'approve_and_pay', p['reason'], previous_amount=p['original'], amount=p['amount'],
              previous_status=req.approval_status)
        req.update(dict(amount=p['amount'], approval_status='Approved', approved_by=frappe.session.user,
                        approved_on=now_datetime()))
        _save(req)
        requests.append(req)
        batch.append('rows', dict(request=req.name, employee=req.employee, employee_name=req.employee_name, amount=req.amount))
    audit(batch, 'confirm_payment', total=batch.total)
    _save(batch)
    for req in requests:
        req.update(dict(payment_status='Paid', payout_batch=batch.name, paid_by=batch.paid_by, paid_on=batch.paid_on))
        _save(req)
    if batch.generate_journal_entry:
        from .accounting import queue_journal
        queue_journal(batch.name)
    return _batch_result(batch)


def _batch_result(batch):
    return dict(batch=batch.name, total=batch.total, status=batch.status, accounting_status=batch.accounting_status)


@frappe.whitelist(methods=['POST'])
@atomic
def manage_requests(work_call, work_date, rows, action, reason=None):
    if action not in ('approve', 'reject', 'amount', 'reconsider'):
        _fail('Acción inválida.')
    if action in ('reject', 'amount', 'reconsider') and not str(reason or '').strip():
        _fail('Indique el motivo de la acción.')
    call, date, cfg, prepared = _prepare(work_call, work_date, rows, lock=True, payable=False)
    for p in prepared:
        req = p['req']
        if not req:
            _fail('Seleccione solicitudes existentes.')
        _rule(check_transition, req, action)
        if req.overtime_work_call != call.name and not (action == 'reconsider' and req.approval_status == 'Cancelled'):
            _fail('Gestione esta solicitud desde su convocatoria de origen.')
    for p in prepared:
        req = p['req']
        audit(req, action, reason or p['reason'], previous_status=req.approval_status,
              previous_amount=req.amount, amount=p['amount'])
        if action == 'approve':
            req.update(dict(approval_status='Approved', amount=p['amount'], approved_by=frappe.session.user, approved_on=now_datetime()))
        elif action == 'reject':
            req.approval_status = 'Rejected'
        elif action == 'amount':
            req.amount = p['amount']
        else:
            req.update(dict(approval_status='Pending', approved_by=None, approved_on=None,
                            overtime_work_call=call.name, authorization=p['auth'].name))
        _save(req)
    return {'updated': len(prepared)}


def _history(call):
    batches = frappe.get_all(BATCH, filters={'overtime_work_call': call.name}, pluck='name', order_by='creation desc')
    result = []
    for name in batches:
        batch = frappe.get_doc(BATCH, name)
        if not access.batch_permission(batch):
            continue  # Never leak other managers' employees, totals or attachments.
        result.append(dict(name=name, status=batch.status, work_date=str(batch.work_date),
            payment_date=str(batch.payment_date), mode_of_payment=batch.mode_of_payment, reference=batch.reference,
            evidence=batch.evidence, currency=batch.currency, total=batch.total, paid_by=batch.paid_by, paid_on=str(batch.paid_on),
            accounting_status=batch.accounting_status, accounting_error=batch.accounting_error,
            rows=[dict(employee=r.employee, employee_name=r.employee_name, amount=r.amount) for r in batch.rows],
            audit=json.loads(batch.audit_log or '[]')))
    return result


@frappe.whitelist()
def payment_history(work_call):
    return _history(_call(work_call, active=False))


@frappe.whitelist()
def my_dietas():
    if frappe.session.user == 'Guest':
        frappe.throw('Inicie sesión.', frappe.PermissionError)
    employees = frappe.get_all('Employee', filters={'user_id': frappe.session.user}, pluck='name')
    requests, eligible = [], []
    for name in employees:
        emp = _employee(name, manage=False)
        for key in frappe.get_all(REQUEST, filters={'employee': name}, pluck='name', order_by='work_date desc'):
            req = frappe.get_doc(REQUEST, key)
            requests.append(dict(name=key, employee=name, employee_name=emp.employee_name,
                work_date=str(req.work_date), amount=req.amount, currency=req.currency, approval_status=req.approval_status,
                payment_status=req.payment_status, review_required=req.review_required,
                audit=json.loads(req.audit_log or '[]')))
        for auth in frappe.get_all('Overtime Authorization', filters={'employee': name, 'docstatus': 1},
                                   fields=['name', 'overtime_work_call', 'work_date']):
            if not auth.overtime_work_call or _request(emp.company, name, auth.work_date):
                continue
            call = _call(auth.overtime_work_call, check_read=False, active=False)
            if call.docstatus != 1 or not any(getdate(r.work_date) == getdate(auth.work_date) and cint(r.get('allows_dieta')) for r in call.dates):
                continue
            if not frappe.db.exists('Dieta Company Settings', {'parent': 'IGC Settings', 'company': emp.company, 'enabled': 1}):
                continue
            cfg = settings(emp.company)
            eligible.append(dict(authorization=auth.name, work_date=str(auth.work_date),
                employee_name=emp.employee_name, amount=cfg.default_amount, currency=cfg.currency))
    return {'requests': requests, 'eligible': eligible}


@frappe.whitelist(methods=['POST'])
@atomic
def request_dieta(authorization, notes=None):
    source = frappe.get_doc('Overtime Authorization', authorization)
    emp = _employee(source.employee, manage=False)
    call = _call(source.overtime_work_call, lock=True, check_read=False)
    frappe.db.get_value('Employee', emp.name, 'name', for_update=True)
    date = _eligible_date(call, source.work_date)
    emp = _employee(emp.name, manage=False, lock=True)
    source = _authorization(call, emp, date, lock=True)
    existing = _request(call.company, emp.name, date, lock=True)
    if existing:
        return {'request': existing.name}
    cfg = settings(call.company, lock=True)
    req = _new_request(call, date, cfg, dict(emp=emp, auth=source, amount=cfg.default_amount), 'Employee')
    req.notes = str(notes or '')
    _save(req)
    return {'request': req.name}
