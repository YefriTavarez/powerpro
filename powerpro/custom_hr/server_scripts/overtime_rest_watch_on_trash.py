# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    frappe.throw(_('Conserve el seguimiento del descanso y su historial.'), frappe.PermissionError)

run(doc)
