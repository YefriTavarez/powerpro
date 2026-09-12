"""A settings save publishes an immutable company policy, never payroll."""
import frappe
from frappe import _
from frappe.utils import cint, getdate
from powerpro.controllers.overtime_pay_policy import active_revisions, policy_rows
from powerpro.payroll_rules.overtime_pay_policy import validate_policy

SETTING_MAP = {
    'company': 'overtime_policy_company',
    'valid_from': 'overtime_policy_from',
    'valid_until': 'overtime_policy_until',
    'weekly_threshold': 'overtime_policy_weekly_threshold',
    'regular_percent': 'overtime_policy_regular_percent',
    'extraordinary_percent': 'overtime_policy_extraordinary_percent',
    'night_percent': 'overtime_policy_night_percent',
    'weekly_rest_cash': 'overtime_policy_weekly_rest_cash',
    'weekly_rest_percent': 'overtime_policy_weekly_rest_percent',
    'auto_ordinary_night': 'overtime_policy_auto_ordinary_night',
    'enable_compensatory': 'overtime_policy_compensatory',
    'leave_type': 'overtime_policy_leave_type',
    'hours_per_leave_day': 'overtime_policy_hours_per_day',
    'leave_increment': 'overtime_policy_leave_increment',
    'rest_hours_per_worked_hour': 'overtime_policy_rest_factor',
    'weekly_rest_duration_hours': 'overtime_policy_rest_duration',
    'weekly_rest_credit_hours': 'overtime_policy_rest_credit',
}
NUMBERS = set(SETTING_MAP) - {'company', 'valid_from', 'valid_until', 'leave_type'}


def values(settings):
    result = {key: settings.get(field) for key, field in SETTING_MAP.items()}
    # Singles upgraded with new fields may return None until their first save.
    # Persist explicit numeric values so Document defaults cannot create a revision on retry.
    for key in NUMBERS: result[key] = float(result[key] or 0)
    result['night_basis'] = ('Whole nocturnal session' if cint(settings.get('overtime_policy_whole_night'))
                             else 'Clock overlap')
    result['premium_combination'] = 'Additive on base hour'
    return result


def same_rules(policy, data):
    for key, value in data.items():
        actual = policy.get(key)
        if key in NUMBERS:
            if float(actual or 0) != float(value or 0): return False
        elif key in {'valid_from', 'valid_until'}:
            if getdate(actual) != getdate(value): return False
        elif (actual or '') != (value or ''):
            return False
    return True


def validate_settings(settings):
    if not cint(settings.get('manage_overtime_pay_policy')): return
    # This is an approval operation as well as a Single write. Check both rights.
    if not frappe.has_permission('DGII Payroll Settings', 'write'):
        frappe.throw(_('No tiene permiso para configurar las reglas de nómina.'), frappe.PermissionError)
    if not frappe.has_permission('Overtime Pay Policy', 'create') or not frappe.has_permission('Overtime Pay Policy', 'submit'):
        frappe.throw(_('No tiene permiso para publicar políticas de horas extra.'), frappe.PermissionError)
    data = values(settings)
    try:
        validate_policy(dict(data, approval_reference='Settings save'))
    except ValueError as exc:
        frappe.throw(str(exc))
    if data['enable_compensatory'] and not frappe.db.get_value('Leave Type', data['leave_type'], 'is_compensatory'):
        frappe.throw(_('El tipo de licencia debe permitir descanso compensatorio.'))
    frappe.get_doc('Company', data['company']).check_permission('read')


def publish(settings):
    if not cint(settings.get('manage_overtime_pay_policy')): return
    validate_settings(settings)
    data = values(settings)
    # Serialize all entry points (settings and native policy submit) by company.
    frappe.db.get_value('Company', data['company'], 'name', for_update=True)
    current = active_revisions(policy_rows(data['company'], data['valid_from'], data['valid_until'], for_update=True))
    previous = None
    if current:
        if (len(current) != 1 or getdate(current[0].valid_from) != getdate(data['valid_from'])
                or getdate(current[0].valid_until) != getdate(data['valid_until'])):
            frappe.throw(_('La vigencia coincide parcialmente con otras reglas. Use sus fechas exactas o un período sin superposición.'))
        previous = frappe.get_doc('Overtime Pay Policy', current[0].name, for_update=True)
        previous.check_permission('read')
        if settings.get('overtime_policy_version') != previous.name:
            frappe.throw(_('Otra versión ya está vigente. Selecciónela y use Cargar reglas de la versión antes de guardar.'))
        if same_rules(previous, data): return
    note = (settings.get('overtime_policy_change_note') or '').strip()
    reference = _('Configuración guardada por {0}.').format(frappe.session.user)
    if note: reference += '\n' + note
    policy = frappe.get_doc(dict(data, doctype='Overtime Pay Policy',
        title=_('Reglas de {0}: {1} a {2}').format(data['company'], data['valid_from'], data['valid_until']),
        approval_reference=reference, supersedes=previous.name if previous else None))
    policy.insert()
    policy.submit()
    settings.db_set('overtime_policy_version', policy.name, update_modified=False)


@frappe.whitelist()
def load_version(name):
    """Permission-scoped read used by the settings editor; it does not save."""
    if not frappe.has_permission('DGII Payroll Settings', 'write'):
        frappe.throw(_('No tiene permiso para configurar las reglas de nómina.'), frappe.PermissionError)
    policy = frappe.get_doc('Overtime Pay Policy', name)
    policy.check_permission('read')
    if policy.docstatus != 1: frappe.throw(_('Seleccione una versión aprobada.'))
    data = {field: policy.get(key) for key, field in SETTING_MAP.items()}
    data['overtime_policy_whole_night'] = int(policy.night_basis == 'Whole nocturnal session')
    data['overtime_policy_version'] = policy.name
    return data
