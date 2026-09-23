# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    frappe.throw(_('Utilice las acciones auditadas para programar y confirmar el descanso.'))

run(doc)
