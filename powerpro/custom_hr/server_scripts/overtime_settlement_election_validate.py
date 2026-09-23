# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    if doc.docstatus == 2:
        return
    if bool(doc.authorization) == bool(doc.retroactive_adjustment):
        frappe.throw(_('Indique exactamente una autorización o un ajuste retroactivo como origen.'))
    auth = frappe.get_doc('Overtime Authorization', doc.authorization) if doc.authorization else frappe.get_doc('Retroactive Overtime Adjustment', doc.retroactive_adjustment)
    auth.check_permission('read')
    try:
        doc.update(doc.evaluate_election(auth))
    except ValueError as exc:
        frappe.throw(str(exc))
    if doc.docstatus == 0:
        doc.active_authorization = None
        doc.active_weekly_rest = None
        doc.approved_by = None
        doc.approved_on = None
        doc.status = 'Draft'
        doc.leave_application = None
        doc.actual_start = None
        doc.actual_end = None
        doc.enjoyment_reference = None
        doc.confirmed_by = None
        doc.confirmed_on = None

run(doc)
