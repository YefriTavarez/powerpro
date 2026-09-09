"""Deterministic dieta rules, also usable without a Frappe site."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json


def money(value, precision=2):
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number <= 0:
            raise ValueError('El monto de la dieta debe ser positivo.')
        quantum = Decimal(1).scaleb(-int(precision))
        number = number.quantize(quantum, rounding=ROUND_HALF_UP)
        if number <= 0:
            raise ValueError('El monto de la dieta debe ser positivo.')
        return float(number)
    except (InvalidOperation, TypeError):
        raise ValueError('Monto de dieta inválido.') from None


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, separators=(',', ':')).encode()).hexdigest()


def day_key(company, employee, work_date):
    return digest([company, employee, str(work_date)])


def check_payable(request):
    if request and request.get('payment_status') == 'Paid':
        raise ValueError('Esta dieta ya fue pagada.')
    if request and request.get('approval_status') in ('Rejected', 'Cancelled'):
        raise ValueError('Reconsidere la solicitud antes de pagar.')


def check_transition(request, action):
    if request.get('payment_status') == 'Paid':
        raise ValueError('Una dieta pagada no se puede modificar.')
    state = request.get('approval_status')
    allowed = {'approve': {'Pending'}, 'reject': {'Pending', 'Approved'},
               'amount': {'Pending'}, 'reconsider': {'Approved', 'Rejected', 'Cancelled'}}
    if state not in allowed.get(action, set()):
        raise ValueError('La solicitud cambió de estado; actualice la selección.')


def override_required(old, new):
    return money(old) != money(new)
