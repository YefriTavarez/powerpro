# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    frappe.throw(_('La evidencia enviada es inmutable; cancele y cree una liquidación corregida.'))

run(doc)
