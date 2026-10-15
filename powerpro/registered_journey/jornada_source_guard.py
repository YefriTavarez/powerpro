# Applies only to documents explicitly created by the unified journey flow.
def guard(doc, financial=False):
    name=doc.get('custom_igc_journey')
    if not doc.is_new():
        old=frappe.get_doc(doc.doctype,doc.name)
        if old.get('custom_igc_journey') and any(doc.get(k)!=old.get(k) for k in ['custom_igc_journey','custom_igc_journey_row','custom_igc_journey_key']):
            frappe.throw('El vínculo original con Registro de Jornada se conserva como historial.')
    if not name:
        return
    register=frappe.get_doc('Registro de Jornada',name)
    register.check_permission('read')
    row=None
    for item in register.employees:
        if item.name==doc.get('custom_igc_journey_row'):
            row=item
    if not row or doc.get('custom_igc_journey_key')!=register.name+'|'+row.name:
        frappe.throw('El vínculo con Registro de Jornada no es válido.')
    if doc.doctype!='Overtime Work Call' and doc.employee!=row.employee:
        frappe.throw('El empleado no coincide con la jornada de origen.')
    day=frappe.utils.getdate(register.starts_at)
    if doc.doctype=='Shift Assignment':
        if doc.shift_type!=register.replacement_shift or frappe.utils.getdate(doc.start_date)!=day or not doc.end_date or frappe.utils.getdate(doc.end_date)!=day:
            frappe.throw('La asignación temporal debe corresponder al turno y fecha de su Registro de Jornada.')
        if doc.docstatus in [1,2] and financial:
            if doc.docstatus==1:
                try:
                    support=frappe.call('powerpro.controllers.registered_journey.capabilities')
                except Exception:
                    frappe.throw('Falta desplegar el soporte de jornadas históricas en PowerPro antes de validar esta asignación.')
                if not support or support.get('version')!=1:
                    frappe.throw('Versión de PowerPro incompatible con la asignación temporal.')
            frappe.db.get_value('Employee',doc.employee,'name',for_update=True)
            week_start=frappe.utils.add_days(day,-day.weekday())
            week_end=frappe.utils.add_days(week_start,6)
            for dt in ['Overtime Authorization','Retroactive Overtime Adjustment','Ordinary Night Settlement']:
                if frappe.db.exists(dt,{'employee':row.employee,'docstatus':1,'work_date':['between',[week_start,week_end]]}):
                    frappe.throw('Existen autorizaciones o liquidaciones aprobadas en esa semana. Revise sus dependencias antes del cambio de turno.')
        return
    if doc.doctype=='Overtime Work Call':
        if len(doc.employees or [])!=1 or doc.employees[0].employee!=row.employee:
            frappe.throw('La convocatoria debe conservar el empleado de su Registro de Jornada.')
        if len(doc.dates or [])!=1:
            frappe.throw('La convocatoria debe conservar una sola jornada.')
        item=doc.dates[0]
        a=frappe.utils.get_datetime(str(item.work_date)+' '+str(item.start_time))
        b=frappe.utils.get_datetime(str(item.work_date)+' '+str(item.end_time))
        if b<=a:b=frappe.utils.add_to_date(b,days=1)
        if a!=frappe.utils.get_datetime(register.starts_at) or b!=frappe.utils.get_datetime(register.ends_at) or frappe.utils.getdate(doc.automatic_payroll_date)!=frappe.utils.getdate(register.payroll_date):
            frappe.throw('El horario y la fecha de nómina deben corresponder a la jornada registrada.')
        if doc.planned_settlement!='Cash' or doc.automation_mode!='Verified Checkins' or doc.evidence_auto_settle:
            frappe.throw('La convocatoria vinculada conserva su conciliación por marcaciones y liquidación revisada.')
        return
    if frappe.utils.getdate(doc.work_date)!=day or frappe.utils.getdate(doc.settlement_payroll_date)!=frappe.utils.getdate(register.payroll_date):
        frappe.throw('La fecha trabajada y la fecha de nómina deben corresponder al Registro de Jornada.')
    if doc.doctype=='Retroactive Overtime Adjustment':
        if doc.reconciliation_engine!='Verified Checkins' or doc.historical_documentation:
            frappe.throw('Esta jornada requiere el proceso de conciliación y liquidación por marcaciones.')
        if frappe.utils.get_datetime(doc.authorization_start)!=frappe.utils.get_datetime(register.starts_at) or frappe.utils.get_datetime(doc.authorization_end)!=frappe.utils.get_datetime(register.ends_at):
            frappe.throw('El intervalo debe corresponder a la jornada registrada.')
    if doc.docstatus!=1 or not financial:
        return
    if register.payroll_entry and frappe.db.get_value('Payroll Entry',register.payroll_entry,'docstatus')!=0:
        frappe.throw('La nómina de destino ya no está en borrador. Revise la fecha de liquidación antes de continuar.')
    mode=row.break_mode or 'Marcaciones'
    if mode=='Descanso Flexible del Turno':
        frappe.throw('El descanso flexible está registrado, pero falta verificar su aplicación al cálculo. Revise la evidencia antes de liquidar.')
    evidence=json.loads(doc.evidence_snapshot or '{}')
    intervals=evidence.get('worked_intervals') or []
    if not intervals:
        frappe.throw('Falta la evidencia completa de la jornada para revisar el descanso.')
    if mode=='Descanso Declarado':
        if not row.actual_start or not row.actual_end or not row.break_start or not row.break_end or not row.evidence_reference:
            frappe.throw('Complete la declaración y su referencia antes de aprobar.')
        expected=[]
        start=str(frappe.utils.get_datetime(row.actual_start))
        end=str(frappe.utils.get_datetime(row.actual_end))
        ba=str(frappe.utils.get_datetime(row.break_start))
        bb=str(frappe.utils.get_datetime(row.break_end))
        if start<ba:expected.append({'start':start,'end':ba})
        if bb<end:expected.append({'start':bb,'end':end})
        actual=[{'start':str(frappe.utils.get_datetime(r['start'])),'end':str(frappe.utils.get_datetime(r['end']))} for r in intervals]
        if actual!=expected:
            frappe.throw('La evidencia del cálculo no coincide con el horario y descanso declarados. Acepte primero la revisión nativa de la jornada.')
    else:
        shift=frappe.get_doc('Shift Type',doc.shift_type)
        if frappe.utils.flt(shift.get('custom_duracion_break_minutos'))>0:
            span=(frappe.utils.get_datetime(intervals[-1]['end'])-frappe.utils.get_datetime(intervals[0]['start'])).total_seconds()
            worked=sum([(frappe.utils.get_datetime(r['end'])-frappe.utils.get_datetime(r['start'])).total_seconds() for r in intervals])
            if span-worked<60:
                frappe.throw('Las marcaciones todavía no identifican el descanso. Revise la jornada antes de liquidar; no se asumirá que trabajó durante toda la pausa.')

guard(doc, FINANCIAL_GUARD)
