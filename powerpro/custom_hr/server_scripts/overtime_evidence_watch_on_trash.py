# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    frappe.throw(_('Conserve el seguimiento y su historial de cambios.'), frappe.PermissionError)

run(doc)
