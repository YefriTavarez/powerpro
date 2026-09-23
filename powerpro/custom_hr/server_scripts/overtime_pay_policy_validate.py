# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    if (doc.get('holiday_weekly_rest_mode') or 'Require review') not in {'Require review', 'Single highest premium', 'Additive premiums'}:
        frappe.throw('Seleccione una regla admitida para feriado y descanso semanal.')
    if not doc.get('company') or not doc.get('valid_from') or (not doc.get('valid_until')):
        frappe.throw('Indique empresa y vigencia de la política.')
    if frappe.utils.get_datetime(str(doc.get('valid_until'))) < frappe.utils.get_datetime(str(doc.get('valid_from'))):
        frappe.throw('La fecha final de vigencia debe ser posterior o igual al inicio.')
    if not str(doc.get('approval_reference') or '').strip():
        frappe.throw('Documente la aprobación de estas reglas y sus ejemplos de cálculo.')
    for key, minimum in [('regular_percent', 35), ('extraordinary_percent', 100), ('night_percent', 15), ('weekly_rest_percent', 100)]:
        value = float(doc.get(key) or 0)
        if not (float("-inf") < value < float("inf")) or value < minimum:
            frappe.throw(f'{key}: el porcentaje no puede ser inferior a {minimum}.')
    threshold = float(doc.get('weekly_threshold') or 0)
    if not (float("-inf") < threshold < float("inf")) or not 0 < threshold <= 68:
        frappe.throw('El umbral semanal debe ser positivo y no superar 68 horas.')
    if doc.get('night_basis') not in {'Clock overlap', 'Whole nocturnal session'}:
        frappe.throw('Seleccione expresamente la regla de nocturnidad aprobada.')
    if doc.get('premium_combination') != 'Additive on base hour':
        frappe.throw('La combinación de recargos debe tener una regla implementada y aprobada.')
    if doc.get('holiday_weekly_rest_compensatory') and (not doc.get('enable_compensatory')):
        frappe.throw('Habilite descanso compensatorio antes de combinarlo con el pago de feriado.')
    if doc.get('enable_compensatory'):
        if not doc.get('leave_type'):
            frappe.throw('Indique el tipo de licencia del descanso compensatorio.')
        for field in ['hours_per_leave_day', 'leave_increment']:
            value = float(doc.get(field) or 0)
            if not (float("-inf") < value < float("inf")) or value <= 0:
                frappe.throw(f'{field} debe ser positivo y finito.')
        factor = float(doc.get('rest_hours_per_worked_hour') or 0)
        if not (float("-inf") < factor < float("inf")) or factor < 1:
            frappe.throw('Defina al menos una hora de descanso por hora compensada.')
        if float(doc.get('leave_increment')) not in {0.5, 1}:
            frappe.throw('La licencia nativa admite incrementos de medio día o día completo en esta versión.')
    if doc.docstatus == 0:
        doc.approved_by = None
        doc.approved_on = None

run(doc)
