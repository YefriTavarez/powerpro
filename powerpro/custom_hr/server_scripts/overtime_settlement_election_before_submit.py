# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    if not doc.is_managed_action('submit'):
        frappe.throw(_('Utilice las acciones de elección y descanso.'), frappe.PermissionError)
    if bool(doc.authorization) == bool(doc.retroactive_adjustment):
        frappe.throw(_('Indique exactamente una autorización o un ajuste retroactivo como origen.'))
    auth = frappe.get_doc('Overtime Authorization', doc.authorization, for_update=True) if doc.authorization else frappe.get_doc('Retroactive Overtime Adjustment', doc.retroactive_adjustment, for_update=True)
    doc.previous_method = auth.planned_settlement
    if doc.locked_rows(doc.doctype, filters={'active_authorization': (auth.name if auth.doctype == 'Overtime Authorization' else 'Retroactive Overtime Adjustment|' + auth.name)}, pluck='name', limit=1):
        frappe.throw(_('Ya hay una elección activa para esta autorización.'))
    doc.active_authorization = (auth.name if auth.doctype == 'Overtime Authorization' else 'Retroactive Overtime Adjustment|' + auth.name)
    if doc.weekly_rest:
        date = frappe.utils.getdate(auth.work_date)
        week = str(frappe.utils.add_days(date, -date.weekday()))
        doc.rest_week = week
        others = doc.locked_rows(doc.doctype, filters={'employee': doc.employee, 'rest_week': week, 'docstatus': 1, 'active_authorization': ['is', 'set']}, fields=['choice'])
        if others and (doc.choice == 'Compensatory Rest' or any((r.choice == 'Compensatory Rest' for r in others))):
            frappe.throw(_('El descanso semanal ya tiene una elección incompatible o un crédito; consolide la obligación antes de liquidar.'))
        if doc.choice == 'Compensatory Rest':
            doc.active_weekly_rest = doc.claim_digest(doc.employee + '|' + week)
    if doc.choice == 'Compensatory Rest':
        overlaps = doc.locked_rows(doc.doctype, filters=[['employee', '=', doc.employee], ['docstatus', '=', 1], ['active_authorization', 'is', 'set'], ['choice', '=', 'Compensatory Rest'], ['planned_start', '<', doc.planned_end], ['planned_end', '>', doc.planned_start]], pluck='name', limit=1)
        if overlaps:
            frappe.throw(_('El mismo intervalo de descanso no puede cumplir dos obligaciones.'))
    doc.approved_by = frappe.session.user
    doc.approved_on = frappe.utils.now_datetime()
    doc.status = 'Approved'

run(doc)
