"""Apply only the two business-role grants on a site with custom DocPerm rows.

Call apply() from an initialized Administrator session after reviewing the site.
The caller owns commit/rollback. No roles, users or business records are created.
The standard DocType JSON carries the same permissions for sites without overrides.
"""
import frappe

ROLES = ('Gerente Finanzas', 'Encargado Gestión Humana')
GRANTS = ('read', 'create', 'report', 'print')


def apply():
    if frappe.session.user != 'Administrator':
        frappe.throw('Esta configuración requiere Administrator.', frappe.PermissionError)
    for role in ROLES:
        if not frappe.db.exists('Role', role):
            frappe.throw('El rol debe existir antes de aplicar permisos: ' + role)
    changed = []
    for role in ROLES:
        rows = frappe.get_all('Custom DocPerm', filters={
            'parent': 'Solicitud de Dieta', 'role': role, 'permlevel': 0}, pluck='name')
        if len(rows) > 1:
            frappe.throw('Revise los permisos duplicados para ' + role)
        if rows:
            doc = frappe.get_doc('Custom DocPerm', rows[0])
            if doc.if_owner:
                frappe.throw('Revise la restricción de propietario para ' + role)
        else:
            doc = frappe.get_doc(dict(doctype='Custom DocPerm',
                parent='Solicitud de Dieta', role=role, permlevel=0, if_owner=0,
                export=0))
        if doc.is_new() or any(not doc.get(grant) for grant in GRANTS):
            doc.update({grant: 1 for grant in GRANTS})
            doc.save(ignore_permissions=True)
            changed.append(doc.name)
    return changed
