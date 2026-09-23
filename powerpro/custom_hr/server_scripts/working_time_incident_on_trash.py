# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    frappe.throw(_('Conserve la incidencia y su historial de resolución.'), frappe.PermissionError)

run(doc)
