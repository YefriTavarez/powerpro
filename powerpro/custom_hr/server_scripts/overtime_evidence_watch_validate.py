# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    if not doc.is_service_write():
        frappe.throw(_('La bandeja se actualiza mediante una nueva comprobación de evidencia.'), frappe.PermissionError)

run(doc)
