# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    if not doc.is_internal_revision() or not doc.is_new():
        frappe.throw(_('El historial de complementos es inmutable y se registra al actualizar Employee.'), title=_('Complementos de nómina'))

run(doc)
