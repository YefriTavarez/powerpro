# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    frappe.throw('El historial de dietas no se puede renombrar.', frappe.PermissionError)

run(doc)
