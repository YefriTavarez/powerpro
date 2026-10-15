# IGC Registro de Jornada v1: coordination only; native documents own approval and payment.
def validate_record(doc):
    for employee_name in sorted(set([r.employee for r in doc.employees if r.employee])):
        frappe.db.get_value('Employee',employee_name,'name',for_update=True)
    before=doc.get_doc_before_save()
    if before and str(before.modified)!=str(frappe.db.get_value(doc.doctype,doc.name,'modified')):
        frappe.throw('La jornada cambió mientras se guardaba. Actualice antes de continuar.')
    start = frappe.utils.get_datetime(doc.starts_at)
    end = frappe.utils.get_datetime(doc.ends_at)
    if end <= start or (end - start).total_seconds() > 86400:
        frappe.throw('La jornada debe tener inicio y fin, durar como máximo 24 horas y terminar después del inicio.')
    if doc.journey_type not in ['Horas Adicionales', 'Cambio de Turno', 'Cambio de Turno y Horas Adicionales']:
        frappe.throw('Seleccione el tipo de jornada.')
    if doc.journey_type != 'Horas Adicionales' and not doc.replacement_shift:
        frappe.throw('Seleccione el turno que sustituye la jornada ordinaria.')
    if not str(doc.reason or '').strip():
        frappe.throw('Indique el motivo de la jornada.')
    if not doc.payroll_date or frappe.utils.getdate(doc.payroll_date) < start.date():
        frappe.throw('La fecha de nómina debe ser igual o posterior a la fecha trabajada.')
    if doc.payroll_entry:
        payroll = frappe.get_doc('Payroll Entry', doc.payroll_entry)
        payroll.check_permission('read')
        if payroll.docstatus != 0 or payroll.company != doc.company or not (frappe.utils.getdate(payroll.start_date) <= frappe.utils.getdate(doc.payroll_date) <= frappe.utils.getdate(payroll.end_date)):
            frappe.throw('Seleccione una nómina en borrador de la misma empresa que incluya la fecha de pago.')
    if doc.source_work_call:
        source = frappe.get_doc('Overtime Work Call', doc.source_work_call)
        source.check_permission('read')
        if source.company != doc.company:
            frappe.throw('La convocatoria pertenece a otra empresa.')
    if not 1 <= len(doc.employees or []) <= 50:
        frappe.throw('Seleccione entre uno y 50 empleados por jornada.')
    seen = []
    for row in doc.employees:
        if not row.employee or row.employee in seen:
            frappe.throw('Seleccione cada empleado una sola vez.')
        seen.append(row.employee)
        if row.break_mode not in ['Marcaciones','Descanso Flexible del Turno','Descanso Declarado']:
            frappe.throw('Seleccione un modo de descanso válido.')
        employee = frappe.get_doc('Employee', row.employee)
        employee.check_permission('read')
        if employee.company != doc.company:
            frappe.throw('Todos los empleados deben pertenecer a la empresa seleccionada.')
        row.employee_name = employee.employee_name
        if employee.date_of_joining and start.date() < frappe.utils.getdate(employee.date_of_joining):
            frappe.throw('La jornada no puede ser anterior al ingreso de ' + employee.employee_name)
        if employee.relieving_date and start.date() > frappe.utils.getdate(employee.relieving_date):
            frappe.throw('La jornada no puede ser posterior a la salida de ' + employee.employee_name)
        a = frappe.utils.get_datetime(row.actual_start or doc.starts_at)
        b = frappe.utils.get_datetime(row.actual_end or doc.ends_at)
        if a < start or b > end or b <= a:
            frappe.throw('El horario individual debe quedar dentro de la jornada registrada.')
        if bool(row.break_start) != bool(row.break_end):
            frappe.throw('Complete inicio y fin del descanso declarado.')
        if row.break_start:
            ba = frappe.utils.get_datetime(row.break_start)
            bb = frappe.utils.get_datetime(row.break_end)
            if ba < a or bb > b or bb <= ba:
                frappe.throw('El descanso debe quedar dentro del horario individual.')
        if row.work_order:
            order = frappe.get_doc('Work Order', row.work_order)
            order.check_permission('read')
            if order.company != doc.company or order.docstatus == 2:
                frappe.throw('Revise la orden de producción del empleado.')
        if row.job_card:
            card = frappe.get_doc('Job Card', row.job_card)
            card.check_permission('read')
            if not row.work_order or card.work_order != row.work_order or card.docstatus == 2:
                frappe.throw('La Tarjeta de Trabajo debe corresponder a la orden seleccionada.')
    identity = {'company':doc.company, 'journey_type':doc.journey_type, 'starts_at':str(doc.starts_at), 'ends_at':str(doc.ends_at), 'replacement_shift':doc.replacement_shift or '', 'payroll_date':str(doc.payroll_date), 'payroll_entry':doc.payroll_entry or '', 'reason':doc.reason, 'source_work_call':doc.source_work_call or '', 'employees':[]}
    for row in doc.employees:
        identity['employees'].append({k:str(row.get(k) or '') for k in ['employee','work_order','job_card']})
    current = json.dumps(identity, ensure_ascii=False, sort_keys=True)
    previous = None
    if not doc.is_new():
        previous = frappe.get_doc(doc.doctype, doc.name)
        if previous.source_snapshot and previous.source_snapshot != current:
            frappe.throw('La jornada ya tiene documentos preparados. Conserve este registro y tramite cualquier corrección desde los documentos vinculados; para otra jornada cree un registro nuevo.')
        for row in doc.employees:
            for old_row in previous.employees:
                if old_row.name == row.name and any(str(row.get(k) or '') != str(old_row.get(k) or '') for k in ['actual_start','actual_end','break_mode','break_start','break_end','evidence_reference']):
                    for field, dt in [('retroactive_adjustment','Retroactive Overtime Adjustment'), ('night_settlement','Ordinary Night Settlement')]:
                        if old_row.get(field) and frappe.db.get_value(dt,old_row.get(field),'docstatus') == 1:
                            frappe.throw('La evidencia ya tiene una liquidación aprobada. Utilice la revisión trazable del documento original.')
    linked = False
    for row in doc.employees:
        for field, dt in [('shift_assignment','Shift Assignment'), ('retroactive_adjustment','Retroactive Overtime Adjustment'), ('night_settlement','Ordinary Night Settlement'), ('work_call','Overtime Work Call')]:
            name = row.get(field)
            old = None
            if previous:
                for old_row in previous.employees:
                    if old_row.name == row.name:
                        old = old_row.get(field)
            if old and name != old:
                frappe.throw('Los vínculos preparados se conservan como historial.')
            if name:
                native = frappe.get_doc(dt, name)
                native.check_permission('read')
                if native.custom_igc_journey != doc.name or native.custom_igc_journey_row != row.name:
                    frappe.throw('El documento vinculado no pertenece a esta jornada y empleado.')
                if dt != 'Overtime Work Call' and native.employee != row.employee:
                    frappe.throw('El empleado del documento vinculado no coincide.')
                linked = True
    doc.source_snapshot = current if linked else None
    doc.status = 'Documentos Preparados' if linked else 'Borrador'

validate_record(doc)
