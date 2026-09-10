import frappe
from frappe.permissions import get_user_permissions

REQUEST = 'Solicitud de Dieta'
BATCH = 'Lote de Pago de Dietas'


def employee(employee, lock=False):
    return frappe.get_doc('Employee', employee, for_update=lock)


def in_scope(emp, user=None):
    user = user or frappe.session.user
    if user == 'Guest':
        return False
    restrictions = get_user_permissions(user)
    for dt, value in [('Company', emp.company), ('Employee', emp.name), ('Department', emp.department)]:
        rows = restrictions.get(dt) or []
        # Apply explicit scope even when a custom API bypasses generic list permissions.
        if rows and value not in {row.get('doc') for row in rows}:
            return False
    return True


def can_manage(emp, user=None):
    user = user or frappe.session.user
    return bool(user != 'Guest' and emp.user_id != user and in_scope(emp, user) and (
        'HR Manager' in frappe.get_roles(user) or emp.get('expense_approver') == user
    ))


def can_read_request(doc, user=None):
    user = user or frappe.session.user
    emp = employee(doc.employee)
    return bool((user != 'Guest' and emp.user_id == user and in_scope(emp, user)) or can_manage(emp, user))


def can_create_request(doc, user=None):
    user = user or frappe.session.user
    if user == 'Guest' or 'HR Manager' not in frappe.get_roles(user):
        return False
    return not doc.get('employee') or can_manage(employee(doc.employee), user)


def request_permission(doc, user=None, ptype=None, permission_type=None):
    action = ptype or permission_type
    if action == 'create':
        return doc.is_new() and can_create_request(doc, user)
    return action in (None, 'read', 'print', 'report', 'export') and can_read_request(doc, user)


def batch_permission(doc, user=None, ptype=None, permission_type=None):
    user = user or frappe.session.user
    return (ptype or permission_type) in (None, 'read', 'print', 'report', 'export') and bool(doc.rows) and all(
        can_manage(employee(row.employee), user) for row in doc.rows
    )


def visible_employees(user=None, own=True):
    user = user or frappe.session.user
    if user == 'Guest':
        return []
    roles = frappe.get_roles(user)
    filters = {} if 'HR Manager' in roles else {'expense_approver': user}
    names = frappe.get_all('Employee', filters=filters, pluck='name')
    if own:
        names += frappe.get_all('Employee', filters={'user_id': user}, pluck='name')
    return [name for name in set(names) if (
        (own and employee(name).user_id == user and in_scope(employee(name), user))
        or can_manage(employee(name), user)
    )]


def request_query(user=None):
    names = visible_employees(user)
    return ('`tabSolicitud de Dieta`.employee in (' + ','.join(frappe.db.escape(n) for n in names) + ')') if names else '1=0'


def batch_query(user=None):
    names = visible_employees(user, own=False)
    if not names:
        return '1=0'
    quoted = ','.join(frappe.db.escape(n) for n in names)
    return ("EXISTS (SELECT 1 FROM `tabDieta Payout Row` r WHERE r.parent=`tabLote de Pago de Dietas`.name) "
            "AND NOT EXISTS (SELECT 1 FROM `tabDieta Payout Row` r WHERE r.parent=`tabLote de Pago de Dietas`.name "
            f"AND r.employee NOT IN ({quoted}))")
