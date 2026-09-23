# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    frappe.throw(_('El historial de complementos es inmutable y se registra al actualizar Employee.'), title=_('Complementos de nómina'))

run(doc)
