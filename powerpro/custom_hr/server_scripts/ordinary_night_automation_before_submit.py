# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    frappe.db.get_value('Employee', doc.employee, 'name', for_update=True)
    others = doc.locked_rows(doc.doctype, filters=[['employee', '=', doc.employee], ['docstatus', '=', 1], ['from_date', '<=', doc.to_date], ['to_date', '>=', doc.from_date]], pluck='name', limit=1)
    if others:
        frappe.throw(_('Ya existe una programación para este empleado y período: {0}.').replace('{0}', str(others[0])))
    doc.set('days', [])
    start = frappe.utils.getdate(doc.from_date)
    end = frappe.utils.getdate(doc.to_date)
    for offset in range((end - start).days + 1):
        doc.append('days', {'work_date': frappe.utils.add_days(start, offset), 'status': 'Pending'})
    doc.approved_by = frappe.session.user
    doc.approved_on = frappe.utils.now_datetime()
run(doc)
