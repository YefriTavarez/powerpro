"""Cost-center selection for new payouts; no employee or settings writes."""
import frappe


def can_select(center):
    return any(frappe.has_permission('Cost Center', ptype, doc=center)
               for ptype in ('select', 'read'))


def validate(name, company, *, check_permission=False, lock=False):
    if not isinstance(name, str) or not name.strip():
        frappe.throw('Seleccione un centro de costo de movimiento.')
    if lock:
        exists = frappe.db.get_value('Cost Center', name, 'name', for_update=True)
    else:
        exists = frappe.db.exists('Cost Center', name)
    if not exists:
        frappe.throw('El centro de costo seleccionado no existe.')
    center = frappe.get_doc('Cost Center', name, for_update=lock)
    if check_permission and not can_select(center):
        frappe.throw('No tiene permiso para seleccionar este centro de costo.', frappe.PermissionError)
    if center.is_group:
        frappe.throw(f'El centro de costo {name} es un grupo. Seleccione un centro de costo de movimiento.')
    if center.disabled:
        frappe.throw(f'El centro de costo {name} está deshabilitado.')
    if center.company != company:
        frappe.throw('El centro de costo debe pertenecer a la compañía de la dieta.')
    return center.name


def suggested(employee):
    name = employee.get('payroll_cost_center')
    if not name or not frappe.db.exists('Cost Center', name):
        return None
    center = frappe.get_doc('Cost Center', name)
    if (center.company == employee.company and not center.is_group
            and not center.disabled and can_select(center)):
        return center.name
    return None


def prepare(prepared, selections, cfg, *, lock=False):
    """Validate explicit choices only at payout, never at request approval."""
    if not cfg.generate_journal_entry:
        for row in prepared:
            row['cost_center'] = None
        return
    choices = {r['employee']: r.get('cost_center') for r in selections}
    missing = [p['emp'].employee_name for p in prepared
               if not isinstance(choices[p['emp'].name], str) or not choices[p['emp'].name].strip()]
    if missing:
        frappe.throw('Seleccione un centro de costo para: ' + ', '.join(missing))
    # All callers acquire Employee and configuration locks first, then centers.
    # Re-read under the row lock so concurrent edits cannot invalidate the check.
    for name in sorted(set(choices.values())):
        validate(name, cfg.company, check_permission=True, lock=lock)
    for row in prepared:
        row['cost_center'] = choices[row['emp'].name]
