# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    if not doc.flags.get('dieta_service'):
        if doc.is_new():
            doc.validate_new_request()
        else:
            frappe.throw('Utilice los diálogos de Dietas.', frappe.PermissionError)

run(doc)
