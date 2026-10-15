# IGC unified journey coordinator v1. All approvals, evidence and payments stay native.
def fail(message):
    frappe.throw(message)

def require_engine():
    try:
        support=frappe.call('powerpro.controllers.registered_journey.capabilities')
    except Exception:
        fail('Falta desplegar la actualización de PowerPro para Registro de Jornada. El registro puede guardarse, pero todavía no se prepararán turnos ni liquidaciones desde esta pantalla.')
    if not support or support.get('version')!=1:
        fail('La versión de PowerPro no es compatible con este Registro de Jornada.')

def source_doc(dt, name, permission='read'):
    item = frappe.get_doc(dt, name)
    item.check_permission(permission)
    return item

def period_check(record):
    if record.payroll_entry:
        payroll = source_doc('Payroll Entry', record.payroll_entry)
        if payroll.docstatus != 0:
            fail('La nómina seleccionada ya no está en borrador. Revise la fecha de pago desde el documento de liquidación.')

def shift_at(employee, day, locked=False):
    if frappe.db.exists('Shift Assignment',{'employee':employee.name,'docstatus':1,'custom_igc_journey':['is','set']}):
        require_engine()
        return frappe.call('powerpro.controllers.registered_journey.resolve_shift',employee=employee.name,day=str(day))
    rows = frappe.db.sql('SELECT name, shift_type, end_date FROM `tabShift Assignment` WHERE employee=%s AND docstatus=1 AND status=%s AND start_date<=%s ORDER BY start_date DESC, creation DESC LIMIT 1001'+(' FOR UPDATE' if locked else ''), [employee.name,'Active',day], as_dict=True)
    if len(rows)>1000:
        fail('Hay demasiadas asignaciones de turno para revisar.')
    active = [r for r in rows if not r.end_date or frappe.utils.getdate(r.end_date)>=day]
    if len(set([r.shift_type for r in active]))>1:
        fail('Hay asignaciones de turno superpuestas; revíselas primero.')
    return {'name':active[0].name if active else None,'shift':active[0].shift_type if active else employee.default_shift}

def current_row(record, row_name):
    for row in record.employees:
        if row.name == row_name:
            return row
    fail('El empleado no pertenece a esta jornada.')

def native_links(row):
    result=[]
    for field,dt in [('shift_assignment','Shift Assignment'),('retroactive_adjustment','Retroactive Overtime Adjustment'),('night_settlement','Ordinary Night Settlement'),('work_call','Overtime Work Call')]:
        if row.get(field):
            obj=source_doc(dt,row.get(field))
            result.append({'field':field,'doctype':dt,'name':obj.name,'docstatus':obj.docstatus,'status':obj.get('status'),'settlement_status':obj.get('settlement_status'),'payroll_date':str(obj.get('settlement_payroll_date') or obj.get('automatic_payroll_date') or '')})
    return result

def row_info(record,row):
    employee=source_doc('Employee',row.employee)
    day=frappe.utils.getdate(record.starts_at)
    resolved=shift_at(employee,day)
    shift_name=record.replacement_shift if record.journey_type!='Horas Adicionales' else resolved['shift']
    shift=source_doc('Shift Type',shift_name) if shift_name else None
    links=native_links(row)
    warnings=[]
    if employee.status!='Active':warnings.append('El empleado está inactivo; el proceso nativo debe revisar la liquidación histórica.')
    if record.journey_type!='Cambio de Turno':
        approver=employee.get('overtime_approver')
        if not approver or not frappe.db.get_value('User',approver,'enabled'):warnings.append('Debe actualizarse el aprobador de horas extras del empleado.')
        elif frappe.db.exists('Employee',{'user_id':approver,'status':['!=','Active']}):warnings.append('El aprobador asignado corresponde a un empleado inactivo. Revise su asignación en Empleado.')
    first=frappe.utils.getdate(record.starts_at)
    last=frappe.utils.getdate(record.ends_at)
    policies=frappe.get_all('Overtime Pay Policy',filters={'company':record.company,'docstatus':1,'valid_from':['<=',last],'valid_until':['>=',first]},fields=['name','valid_from','valid_until','supersedes'],limit_page_length=101)
    if not policies:warnings.append('Falta una política aprobada para estas fechas; no se calculará un importe hasta resolverla.')
    mode=row.break_mode or 'Marcaciones'
    break_minutes=frappe.utils.flt(shift.get('custom_duracion_break_minutos')) if shift else 0
    if mode=='Descanso Flexible del Turno':
        warnings.append('Descanso flexible registrado: '+str(int(break_minutes))+' minutos previstos. Su aplicación requiere confirmar la evidencia o la regla que determine la parte diurna y nocturna; no se inventan marcaciones.')
    if mode=='Descanso Declarado' and not row.break_start:
        warnings.append('Complete el descanso declarado antes de verificar las horas.')
    if record.journey_type!='Horas Adicionales' and resolved['shift']!=record.replacement_shift:
        warnings.append('El cambio de turno todavía no está aplicado para esta fecha.')
    return {'row':row.name,'employee':row.employee,'employee_name':employee.employee_name,'current_shift':resolved['shift'],'target_shift':shift_name,'break_mode':mode,'break_minutes':break_minutes,'approver':employee.get('overtime_approver'),'links':links,'warnings':warnings,'ended':frappe.utils.get_datetime(record.ends_at)<=frappe.utils.now_datetime()}

def check_no_existing(record,row,dt,start,end):
    if dt=='Shift Assignment':
        matches=frappe.db.sql('SELECT name, end_date FROM `tabShift Assignment` WHERE employee=%s AND docstatus<2 AND start_date<=%s LIMIT 1001 FOR UPDATE',[row.employee,start.date()],as_dict=True)
        matches=[r for r in matches if not r.end_date or frappe.utils.getdate(r.end_date)>=start.date()]
    elif dt=='Ordinary Night Settlement':
        matches=frappe.db.sql('SELECT name FROM `tabOrdinary Night Settlement` WHERE employee=%s AND docstatus<2 AND work_date=%s LIMIT 10 FOR UPDATE',[row.employee,start.date()],as_dict=True)
    else:
        matches=[]
        for kind in ['Overtime Authorization','Retroactive Overtime Adjustment']:
            matches.extend(frappe.db.sql('SELECT name FROM `tab'+kind+'` WHERE employee=%s AND docstatus<2 AND authorization_start<%s AND authorization_end>%s LIMIT 10 FOR UPDATE',[row.employee,end,start],as_dict=True))
    if matches:
        fail('Ya existe un registro para esta jornada. Revise '+', '.join([r.name for r in matches])+'. No se creará un duplicado.')

def lock_employee(row):
    frappe.db.get_value('Employee',row.employee,'name',for_update=True)

def prepare(record,row):
    require_engine()
    period_check(record)
    start=frappe.utils.get_datetime(record.starts_at)
    end=frappe.utils.get_datetime(record.ends_at)
    now=frappe.utils.now_datetime()
    employee=source_doc('Employee',row.employee)
    lock_employee(row)
    siblings=frappe.db.sql('SELECT r.parent,r.shift_assignment,r.retroactive_adjustment,r.night_settlement,r.work_call FROM `tabRegistro de Jornada Empleado` r INNER JOIN `tabRegistro de Jornada` p ON p.name=r.parent WHERE r.employee=%s AND r.parent!=%s AND p.starts_at<%s AND p.ends_at>%s LIMIT 1001 FOR UPDATE',[row.employee,record.name,end,start],as_dict=True)
    if len(siblings)>1000:fail('Demasiadas jornadas registradas para revisar los duplicados.')
    for sibling in siblings:
        parent=frappe.db.get_value('Registro de Jornada',sibling.parent,['starts_at','ends_at'],as_dict=True)
        if parent and frappe.utils.get_datetime(parent.starts_at)<end and frappe.utils.get_datetime(parent.ends_at)>start:
            for field,dt in [('shift_assignment','Shift Assignment'),('retroactive_adjustment','Retroactive Overtime Adjustment'),('night_settlement','Ordinary Night Settlement'),('work_call','Overtime Work Call')]:
                if sibling.get(field) and frappe.db.get_value(dt,sibling.get(field),'docstatus') in [0,1]:
                    fail('Ya hay documentos preparados en otra jornada superpuesta: '+sibling.parent+'. Revise ese registro antes de continuar.')
    resolved=shift_at(employee,start.date(),True)
    common={'custom_igc_journey':record.name,'custom_igc_journey_row':row.name,'custom_igc_journey_key':record.name+'|'+row.name}
    if record.journey_type!='Horas Adicionales' and resolved['shift']!=record.replacement_shift:
        if row.shift_assignment:
            return {'notice':'Revise y valide la asignación de turno preparada antes de calcular los recargos.','links':native_links(row)}
        check_no_existing(record,row,'Shift Assignment',start,end)
        assignment=frappe.get_doc({'doctype':'Shift Assignment','employee':row.employee,'company':record.company,'shift_type':record.replacement_shift,'start_date':start.date(),'end_date':start.date(),'status':'Active',**common})
        assignment.check_permission('create')
        assignment.insert()
        row.shift_assignment=assignment.name
        record.save()
        assignment.add_comment('Info','Cambio temporal preparado desde '+record.name+'. Motivo: '+record.reason)
        return {'notice':'Asignación temporal en borrador. Revise y valide el cambio; después prepare las liquidaciones.','links':native_links(row)}
    if row.shift_assignment:
        assignment=source_doc('Shift Assignment',row.shift_assignment)
        if assignment.docstatus!=1:fail('La asignación temporal debe estar validada.')
    if start<=now<end:
        fail('La jornada está en curso. Espere su cierre para el registro retroactivo o utilice una autorización previa existente.')
    if start>now:
        if record.journey_type=='Cambio de Turno':return {'notice':'El turno está aplicado. Una vez finalizada la jornada podrá preparar la nocturnidad.','links':native_links(row)}
        if row.work_call:return {'notice':'La convocatoria ya está preparada.','links':native_links(row)}
        check_no_existing(record,row,'Overtime Authorization',start,end)
        call=frappe.get_doc({'doctype':'Overtime Work Call','company':record.company,'reason':record.reason+'\nRegistro de Jornada: '+record.name,'planned_settlement':'Cash','automation_mode':'Verified Checkins','evidence_auto_settle':0,'automatic_payroll_date':record.payroll_date,'from_date':start.date(),'to_date':start.date(),'custom_block_end_date':end.date(),'default_start_time':str(start)[11:19],'default_end_time':str(end)[11:19],**common})
        call.append('dates',{'work_date':start.date(),'start_time':str(start)[11:19],'end_time':str(end)[11:19],'requested_hours':(end-start).total_seconds()/3600,'allows_dieta':0})
        call.append('employees',{'employee':row.employee,'custom_work_order':row.work_order,'custom_job_card':row.job_card})
        call.check_permission('create')
        call.insert()
        row.work_call=call.name
        record.save()
        return {'notice':'Convocatoria preparada en borrador; conserva su autorización previa habitual.','links':native_links(row)}
    if record.journey_type!='Cambio de Turno' and not row.retroactive_adjustment:
        check_no_existing(record,row,'Retroactive Overtime Adjustment',start,end)
        adjustment=frappe.get_doc({'doctype':'Retroactive Overtime Adjustment','employee':row.employee,'work_date':start.date(),'authorization_start':start,'authorization_end':end,'maximum_hours':(end-start).total_seconds()/3600,'reason':record.reason,'exception_justification':'Registro posterior de jornada documentada en '+record.name+'. '+(row.evidence_reference or record.reason),'planned_settlement':'Cash','settlement_payroll_date':record.payroll_date,'reconciliation_engine':'Verified Checkins','historical_documentation':0,**common})
        adjustment.check_permission('create')
        adjustment.insert()
        row.retroactive_adjustment=adjustment.name
        record.save()
        adjustment.add_comment('Info','Origen '+record.name+'; '+record.journey_type+'; descanso: '+(row.break_mode or 'Marcaciones')+'. '+(row.evidence_reference or ''))
        return {'notice':'Ajuste retroactivo preparado en borrador. Revise la evidencia y su aprobador antes de liquidar.','links':native_links(row)}
    if not row.night_settlement:
        check_no_existing(record,row,'Ordinary Night Settlement',start,end)
        night=frappe.get_doc({'doctype':'Ordinary Night Settlement','employee':row.employee,'work_date':start.date(),'settlement_payroll_date':record.payroll_date,'review_reference':record.name+' · '+record.reason,**common})
        night.check_permission('create')
        # The native service selects policy, shift, salary rate and verified intervals.
        preview=night.build_night_preview()
        if not preview.get('ordinary_hours'):
            return {'notice':'No se identificaron horas nocturnas ordinarias. Revise el ajuste de horas adicionales y su evidencia.','links':native_links(row),'issues':preview.get('issues')}
        if row.break_mode=='Descanso Flexible del Turno':
            fail('El descanso flexible está registrado, pero todavía no hay una declaración o regla aprobada que el cálculo nativo pueda aplicar. Complete la revisión del descanso antes de preparar la nocturnidad.')
        night.insert()
        row.night_settlement=night.name
        record.save()
        return {'notice':'Liquidación nocturna preparada en borrador. Al aprobarla, el proceso nativo creará el Salario Adicional.','links':native_links(row)}
    return {'notice':'Los documentos de esta jornada ya están preparados.','links':native_links(row)}

def apply_shift(record,row):
    require_engine()
    period_check(record)
    if not row.shift_assignment:fail('Prepare primero la asignación temporal.')
    assignment=source_doc('Shift Assignment',row.shift_assignment,'submit')
    if assignment.docstatus==1:return {'notice':'El cambio de turno ya está aplicado.'}
    if assignment.docstatus!=0:fail('La asignación ya no está en borrador.')
    lock_employee(row)
    day=frappe.utils.getdate(record.starts_at)
    # A change must never silently invalidate an already approved weekly settlement.
    week_start=frappe.utils.add_days(day,-day.weekday())
    week_end=frappe.utils.add_days(week_start,6)
    for dt in ['Overtime Authorization','Retroactive Overtime Adjustment','Ordinary Night Settlement']:
        if frappe.db.exists(dt,{'employee':row.employee,'docstatus':1,'work_date':['between',[week_start,week_end]]}):
            fail('Existen autorizaciones o liquidaciones aprobadas en esa semana. Revise su dependencia antes de cambiar el turno histórico.')
    if assignment.shift_type!=record.replacement_shift or frappe.utils.getdate(assignment.start_date)!=day or frappe.utils.getdate(assignment.end_date)!=day:
        fail('La asignación cambió; revise el documento vinculado.')
    assignment.submit()
    assignment.add_comment('Info','Cambio temporal confirmado desde '+record.name+' por '+frappe.session.user+'. Se conservan los ponches originales.')
    return {'notice':'Cambio temporal aplicado únicamente a la fecha registrada.'}

def preview_native(record,row):
    result={'retroactive':None,'night':None}
    if row.retroactive_adjustment:
        result['retroactive']=frappe.call('powerpro.controllers.overtime.get_retroactive_adjustment_preview',adjustment=row.retroactive_adjustment)
    if row.night_settlement:
        night=source_doc('Ordinary Night Settlement',row.night_settlement)
        result['night']={'amount':night.settlement_amount,'hours':night.night_hours,'rate':night.hourly_rate,'percent':night.night_percent,'currency':night.currency,'state':night.evidence_status,'issues':json.loads(night.issues or '[]'),'docstatus':night.docstatus,'settlement_status':night.settlement_status,'additional_salary':night.additional_salary}
    return result

def review_declaration(record,row,apply=False):
    if not row.retroactive_adjustment:fail('Prepare primero el ajuste retroactivo.')
    adjustment=source_doc('Retroactive Overtime Adjustment',row.retroactive_adjustment,'submit')
    if adjustment.docstatus!=0:fail('La declaración inicial requiere un ajuste en borrador. Para correcciones utilice la revisión del documento aprobado.')
    if not row.actual_start or not row.actual_end or not row.evidence_reference:
        fail('Complete el inicio y fin reales y la referencia que respalda la declaración en el detalle del empleado.')
    if row.break_mode!='Descanso Declarado' or not row.break_start or not row.break_end:
        fail('La declaración manual requiere los intervalos efectivamente trabajados. Registre el descanso declarado o revise las marcaciones desde el ajuste; no se presume su ubicación.')
    start=str(frappe.utils.get_datetime(row.actual_start))
    end=str(frappe.utils.get_datetime(row.actual_end))
    ba=str(frappe.utils.get_datetime(row.break_start))
    bb=str(frappe.utils.get_datetime(row.break_end))
    intervals=[]
    if start<ba:intervals.append({'start':start,'end':ba})
    if bb<end:intervals.append({'start':bb,'end':end})
    if not intervals:fail('No quedan horas trabajadas después del descanso.')
    declaration={'full_session':True,'reference':record.name+' · '+row.evidence_reference,'intervals':intervals}
    args={'authorization':adjustment.name,'reason':'Declaración de jornada desde '+record.name+': '+row.evidence_reference,'manual_declaration':json.dumps(declaration,ensure_ascii=False)}
    if apply:
        if frappe.form_dict.get('confirmed')!='1':fail('Confirme la jornada completa antes de aceptar su evidencia.')
        args['token']=frappe.form_dict.get('token')
        return frappe.call('powerpro.controllers.retroactive_draft_review.apply_review',**args)
    return frappe.call('powerpro.controllers.retroactive_draft_review.preview_review',**args)

def import_call(name):
    frappe.new_doc('Registro de Jornada').check_permission('create')
    source=source_doc('Overtime Work Call',name)
    if source.docstatus!=0:fail('La convocatoria ya fue validada. Consulte sus autorizaciones existentes.')
    if len(source.dates or [])!=1:fail('Seleccione una sola jornada de la convocatoria para registrarla; este formulario admite hasta 24 horas por registro.')
    day=source.dates[0]
    start=frappe.utils.get_datetime(str(day.work_date)+' '+str(day.start_time))
    end=frappe.utils.get_datetime(str(day.work_date)+' '+str(day.end_time))
    if end<=start:end=frappe.utils.add_to_date(end,days=1)
    return {'company':source.company,'starts_at':str(start),'ends_at':str(end),'reason':source.reason,'payroll_date':str(source.automatic_payroll_date or frappe.utils.today()),'source_work_call':source.name,'employees':[{'employee':r.employee,'employee_name':r.employee_name,'work_order':r.get('custom_work_order'),'job_card':r.get('custom_job_card'),'break_mode':'Marcaciones'} for r in source.employees]}

action=frappe.form_dict.get('action') or 'details'
if action=='import_call':
    frappe.response['message']=import_call(frappe.form_dict.get('source_work_call'))
else:
    record=source_doc('Registro de Jornada',frappe.form_dict.get('name'),'read' if action in ['details','preview'] else 'write')
    if action=='details':
        frappe.response['message']={'rows':[row_info(record,r) for r in record.employees],'modified':str(record.modified)}
    else:
        row=current_row(record,frappe.form_dict.get('row'))
        if action in ['prepare','apply_shift','review_preview','review_apply']:
            for employee_name in sorted(set([r.employee for r in record.employees])):
                frappe.db.get_value('Employee',employee_name,'name',for_update=True)
            frappe.db.get_value('Registro de Jornada',record.name,'name',for_update=True)
            record.reload()
            row=current_row(record,frappe.form_dict.get('row'))
            if str(record.modified)!=str(frappe.form_dict.get('modified')):fail('La jornada cambió. Actualice antes de continuar.')
            record.check_permission('write')
        if action=='prepare':frappe.response['message']=prepare(record,row)
        elif action=='apply_shift':frappe.response['message']=apply_shift(record,row)
        elif action=='preview':frappe.response['message']=preview_native(record,row)
        elif action=='review_preview':frappe.response['message']=review_declaration(record,row)
        elif action=='review_apply':frappe.response['message']=review_declaration(record,row,True)
        else:fail('Acción no permitida.')
