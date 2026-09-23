# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    frappe.db.get_value('Company', doc.company, 'name', for_update=True)
    if doc.locked_rows('Overtime Pay Policy', filters={'supersedes': doc.name, 'docstatus': 1}, pluck='name', limit=1):
        frappe.throw(_('Esta versión tiene una revisión aprobada. Conserve la cadena de reglas.'))

run(doc)
