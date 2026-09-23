# Editable document-event rules. Python capabilities are not RPC endpoints.
def validate_policy(doc):
    policy = frappe.get_doc('Overtime Pay Policy', doc.policy)
    policy.check_permission('read')
    if policy.docstatus != 1 or policy.company != doc.company or (not frappe.utils.cint(policy.auto_ordinary_night)) or (frappe.utils.getdate(policy.valid_from) > frappe.utils.getdate(doc.from_date)) or (frappe.utils.getdate(policy.valid_until) < frappe.utils.getdate(doc.to_date)):
        frappe.throw(_('Seleccione una política aprobada con nocturnidad automática que cubra este período y empresa.'))

def run(doc, validate_policy):
    if doc.docstatus == 2:
        return
    roles = {line.strip() for line in (frappe.get_doc('DGII Payroll Settings').get('overtime_manual_verification_roles') or '').splitlines() if line.strip()}
    if not roles.intersection(doc.current_roles()):
        frappe.throw(_('Su rol no permite verificar nocturnidad.'), frappe.PermissionError)
    employee = frappe.get_doc('Employee', doc.employee)
    employee.check_permission('read')
    doc.company = employee.company
    start = frappe.utils.getdate(doc.from_date)
    end = frappe.utils.getdate(doc.to_date)
    if not doc.from_date or not doc.to_date or (not 0 <= (end - start).days < 31):
        frappe.throw(_('Programe un período de uno a 31 días.'))
    if not doc.settlement_payroll_date or frappe.utils.getdate(doc.settlement_payroll_date) < end:
        frappe.throw(_('La fecha de nómina debe cubrir todo el período programado.'))
    if not (doc.reference or '').strip():
        frappe.throw(_('Documente la referencia de esta programación.'))
    validate_policy(doc)
    if doc.docstatus == 0:
        doc.approved_by = None
        doc.approved_on = None
        doc.set('days', [])
        start = frappe.utils.getdate(doc.from_date)
        end = frappe.utils.getdate(doc.to_date)
        for offset in range((end - start).days + 1):
            doc.append('days', {'work_date': frappe.utils.add_days(start, offset), 'status': 'Pending'})

run(doc, validate_policy)
