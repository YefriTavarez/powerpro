# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    if not {'System Manager', 'HR Manager'}.intersection(doc.current_roles()):
        frappe.throw(_('Su rol no permite aprobar políticas de horas extra.'), frappe.PermissionError)
    frappe.db.get_value('Company', doc.company, 'name', for_update=True)
    rows = doc.locked_rows('Overtime Pay Policy', filters=[['company', '=', doc.company], ['docstatus', '=', 1], ['valid_from', '<=', doc.valid_until], ['valid_until', '>=', doc.valid_from]], fields=['name', 'supersedes', 'valid_from', 'valid_until'], limit=1001)
    if len(rows) > 1000:
        frappe.throw(_('Demasiadas versiones de reglas para esta vigencia.'))
    replaced = {r.get('supersedes') for r in rows if r.get('supersedes')}
    others = [r for r in rows if r.name not in replaced]
    others = [r for r in others if r.name != doc.name]
    if doc.get('supersedes'):
        if len(others) != 1 or others[0].name != doc.supersedes or frappe.utils.getdate(others[0].valid_from) != frappe.utils.getdate(doc.valid_from) or (frappe.utils.getdate(others[0].valid_until) != frappe.utils.getdate(doc.valid_until)):
            frappe.throw(_('La revisión debe partir de la versión vigente y conservar su empresa y fechas. Recargue las reglas.'))
    elif others:
        frappe.throw(_('Ya existe una política aprobada que se superpone con esta vigencia.'))
    doc.approved_by = frappe.session.user
    doc.approved_on = frappe.utils.now_datetime()

run(doc)
