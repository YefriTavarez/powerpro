# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    frappe.throw(_('Las políticas aprobadas son inmutables; cree una nueva versión con su vigencia.'))

run(doc)
