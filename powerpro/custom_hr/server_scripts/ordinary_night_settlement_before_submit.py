# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    roles = {line.strip() for line in (frappe.get_doc('DGII Payroll Settings').get('overtime_manual_verification_roles') or '').splitlines() if line.strip()}
    if not roles.intersection(doc.current_roles()):
        frappe.throw(_('Su rol no permite verificar nocturnidad.'), frappe.PermissionError)
    settings = frappe.get_doc('DGII Payroll Settings')
    if not frappe.utils.cint(settings.get('enable_checkin_overtime_reconciliation')) or not settings.checkin_overtime_effective_from or frappe.utils.getdate(doc.work_date) < frappe.utils.getdate(settings.checkin_overtime_effective_from):
        frappe.throw(_('La conciliación por marcaciones debe estar habilitada y cubrir esta fecha.'))
    frappe.db.get_value('Employee', doc.employee, 'name', for_update=True)
    current = doc.validate_fresh_evidence()
    if current['input'].get('certified_session') and (not frappe.utils.cint(settings.get('enable_manual_overtime_verification'))):
        frappe.throw(_('La verificación manual debe estar habilitada para liquidar esta declaración.'))
    doc.evidence_snapshot = json.dumps(current, ensure_ascii=False, sort_keys=True, default=str)
    doc.evidence_status = current['state']
    doc.issues = json.dumps(current['issues'], ensure_ascii=False, sort_keys=True, default=str)
    doc.shift_type = current['input']['shift']['name']
    doc.policy = current['input']['policy']['name']
    doc.night_hours = current['ordinary_hours']
    doc.hourly_rate = current['hourly_rate']
    doc.night_percent = current['night_percent']
    doc.settlement_amount = current['amount']
    doc.currency = current['currency']
    doc.company = current['input']['company']
    doc.active_claim = doc.claim_digest(f'{doc.employee}|{frappe.utils.getdate(doc.work_date)}')
    others = doc.locked_rows(doc.doctype, filters={'active_claim': doc.active_claim, 'docstatus': 1}, pluck='name', limit=1)
    if others:
        frappe.throw(_('Ya existe una liquidación nocturna ordinaria para esta jornada.'))
    doc.status = 'Approved'
    doc.approved_by = frappe.session.user
    doc.approved_on = frappe.utils.now_datetime()

run(doc)
