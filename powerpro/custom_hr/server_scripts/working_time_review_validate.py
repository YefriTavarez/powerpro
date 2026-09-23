# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    if not doc.is_service_write():
        frappe.throw(_('Use las acciones de inscripción, pausa y reasignación para conservar la auditoría.'), frappe.PermissionError)

run(doc)
