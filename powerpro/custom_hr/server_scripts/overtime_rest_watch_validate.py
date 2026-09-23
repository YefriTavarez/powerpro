# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    if not doc.is_service_write():
        frappe.throw(_('Use las acciones de seguimiento de descanso.'), frappe.PermissionError)

run(doc)
