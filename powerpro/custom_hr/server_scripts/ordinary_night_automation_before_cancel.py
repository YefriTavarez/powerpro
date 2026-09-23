# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    roles = {line.strip() for line in (frappe.get_doc('DGII Payroll Settings').get('overtime_manual_verification_roles') or '').splitlines() if line.strip()}
    if not roles.intersection(doc.current_roles()):
        frappe.throw(_('Su rol no permite verificar nocturnidad.'), frappe.PermissionError)
    frappe.db.get_value('Employee', doc.employee, 'name', for_update=True)
    before = doc.get_doc_before_save()
    doc.set('days', [row.as_dict() for row in before.days])

run(doc)
