# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    if doc.docstatus == 2:
        return
    if doc.docstatus == 0:
        roles = {line.strip() for line in (frappe.get_doc('DGII Payroll Settings').get('overtime_manual_verification_roles') or '').splitlines() if line.strip()}
        if not roles.intersection(doc.current_roles()):
            frappe.throw(_('Su rol no permite verificar nocturnidad.'), frappe.PermissionError)
        result = doc.build_night_preview()
        doc.company = result['input']['company']
        doc.shift_type = result['input']['shift']['name']
        doc.policy = result['input']['policy']['name']
        doc.evidence_snapshot = json.dumps(result, ensure_ascii=False, sort_keys=True, default=str)
        doc.evidence_status = result['state']
        doc.issues = json.dumps(result['issues'], ensure_ascii=False, sort_keys=True, default=str)
        doc.night_hours = result['ordinary_hours']
        doc.hourly_rate = result['hourly_rate']
        doc.night_percent = result['night_percent']
        doc.settlement_amount = result['amount']
        doc.currency = result['currency']
        doc.status = 'Draft'
        doc.settlement_status = 'Pending'
        doc.active_claim = None
        doc.additional_salary = None
        doc.approved_by = None
        doc.approved_on = None
    if not doc.settlement_payroll_date or frappe.utils.getdate(doc.settlement_payroll_date) < frappe.utils.getdate(doc.work_date):
        frappe.throw(_('La fecha de nómina no puede ser anterior al trabajo.'))

run(doc)
