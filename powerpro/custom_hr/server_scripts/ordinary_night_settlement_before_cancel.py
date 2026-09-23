# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    roles = {line.strip() for line in (frappe.get_doc('DGII Payroll Settings').get('overtime_manual_verification_roles') or '').splitlines() if line.strip()}
    if not roles.intersection(doc.current_roles()):
        frappe.throw(_('Su rol no permite verificar nocturnidad.'), frappe.PermissionError)
    frappe.db.get_value('Employee', doc.employee, 'name', for_update=True)
    doc.check_earnings_cancellable()
    for source_type in ['Overtime Authorization', 'Retroactive Overtime Adjustment']:
        refs = doc.locked_rows(source_type, filters={'employee': doc.employee, 'work_date': doc.work_date, 'docstatus': 1, 'settlement_status': ['in', ['Created', 'Payroll Submitted', 'Paid', 'Credited']]}, fields=['name', 'evidence_snapshot'])
        for ref in refs:
            snapshot = json.loads(ref.evidence_snapshot or '{}')
            if (snapshot.get('ordinary_night_settlement') or {}).get('name') == doc.name:
                frappe.throw(_('Revierta primero las horas extra vinculadas a esta jornada: {0} {1}.').replace('{0}', str(source_type)).replace('{1}', str(ref.name)))
run(doc)
