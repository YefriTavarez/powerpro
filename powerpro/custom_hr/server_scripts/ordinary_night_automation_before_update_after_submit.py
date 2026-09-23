# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    roles = {line.strip() for line in (frappe.get_doc('DGII Payroll Settings').get('overtime_manual_verification_roles') or '').splitlines() if line.strip()}
    if not roles.intersection(doc.current_roles()):
        frappe.throw(_('Su rol no permite verificar nocturnidad.'), frappe.PermissionError)
    if frappe.utils.cint(doc.enabled):
        doc.validate_policy()
    before = doc.get_doc_before_save()
    fields = ['name', 'idx', 'work_date', 'status', 'night_hours', 'amount', 'settlement', 'checked_on', 'summary', 'input_hash', 'issues']
    values = lambda rows: as_json([{key: row.get(key) for key in fields} for row in rows])
    if values(doc.days) != values(before.days):
        frappe.throw(_('El seguimiento diario se actualiza exclusivamente desde el servicio.'))
    if any((doc.get(k) != before.get(k) for k in ['employee', 'company', 'from_date', 'to_date', 'settlement_payroll_date', 'policy', 'reference', 'approved_by', 'approved_on'])):
        frappe.throw(_('La programación aprobada es inmutable; únicamente puede pausarse o reanudarse.'))

run(doc)
