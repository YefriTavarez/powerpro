# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    if not doc.is_managed_action('cancel'):
        frappe.throw(_('Utilice las acciones de elección y descanso.'), frappe.PermissionError)

run(doc)
