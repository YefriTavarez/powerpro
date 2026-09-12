"""Permission-aware overnight preview. No settlement, scheduler or record writes."""
import hashlib
import json
from datetime import datetime,time,timedelta
import frappe
from frappe.utils import get_datetime,getdate,now_datetime
from powerpro.payroll_rules.overtime import get_shift_window
from powerpro.payroll_rules.overtime_overnight import compare_overnight


def get_overnight_comparison(doc):
    start,end=get_datetime(doc.authorization_start),get_datetime(doc.authorization_end)
    if end.date()<=start.date():return {'applicable':False}
    result={'applicable':True,'read_only':True,'settlement_eligible':False,'available':False,'notes':[]}
    if doc.doctype!='Overtime Authorization' or doc.docstatus!=1:
        result['notes']=['Esta interpretación requiere una autorización enviada; los ajustes retroactivos siguen su revisión manual.'];return result
    for dt in ['Employee Checkin','Employee','Shift Assignment','Shift Type']:
        if not frappe.has_permission(dt,'read'):
            result['notes']=['No hay acceso suficiente a las marcaciones y turnos para resolver la madrugada.'];return result
    employees=frappe.get_list('Employee',filters={'name':doc.employee},fields=['name','default_shift'],limit_page_length=1)
    if not employees:
        result['notes']=['No hay acceso al empleado para consultar su contexto de turnos.'];return result
    begin=datetime.combine(start.date(),time.min)
    finish=datetime.combine(end.date()+timedelta(days=1),time.min)
    rows=frappe.get_list('Employee Checkin',filters=[['employee','=',doc.employee],['time','>=',begin],['time','<',finish]],
        fields=['name','time','log_type','shift','shift_start','shift_end','shift_actual_start','shift_actual_end','offshift','skip_auto_attendance','modified'],
        order_by='time asc, name asc',limit_page_length=2001)
    if len(rows)>2000:
        result['notes']=['Demasiadas marcaciones: no se interpreta evidencia truncada.'];return result
    all_checkin_ids=frappe.get_all('Employee Checkin',filters=[['employee','=',doc.employee],['time','>=',begin],['time','<',finish]],pluck='name',limit=2001)
    visible_checkins_complete=len(all_checkin_ids)<=2000 and set(all_checkin_ids)=={r['name'] for r in rows}
    filters={'employee':doc.employee,'docstatus':1,'status':'Active','start_date':['<=',end.date()]}
    or_filters=[['end_date','>=',start.date()],['end_date','is','not set']]
    assignments=frappe.get_list('Shift Assignment',filters=filters,or_filters=or_filters,
        fields=['name','shift_type','start_date','end_date','modified'],limit_page_length=101,order_by='start_date asc, name asc')
    # Internal completeness check exposes no names/data from hidden assignments.
    all_ids=frappe.get_all('Shift Assignment',filters=filters,or_filters=or_filters,pluck='name',limit=101)
    context_complete=visible_checkins_complete and len(assignments)<=100 and set(all_ids)=={r['name'] for r in assignments}
    names={doc.shift_type}|{r['shift_type'] for r in assignments}
    default=employees[0].get('default_shift')
    if default:names.add(default)
    policies=frappe.get_list('Shift Type',filters={'name':['in',sorted(names)]},fields=['name','modified','start_time','end_time',
        'begin_check_in_before_shift_start_time','allow_check_out_after_shift_end_time','last_sync_of_checkin',
        'determine_check_in_and_check_out','working_hours_calculation_based_on'],limit_page_length=len(names),order_by='name asc')
    policy_map={r['name']:r for r in policies}
    if set(policy_map)!=names:context_complete=False
    windows=[]
    day=start.date()+timedelta(days=1)
    while day<=end.date():
        assigned={r['shift_type'] for r in assignments if getdate(r['start_date'])<=day and (not r.get('end_date') or getdate(r['end_date'])>=day)}
        chosen=assigned or ({default} if default else set())
        if not chosen:context_complete=False
        for name in sorted(chosen):
            p=policy_map.get(name)
            if not p:continue
            a,b=get_shift_window(day,p['start_time'],p['end_time'])
            before=float(p.get('begin_check_in_before_shift_start_time') or 0)
            after=float(p.get('allow_check_out_after_shift_end_time') or 0)
            if not a or not b or not 0<=before<=1440 or not 0<=after<=1440:
                context_complete=False;continue
            windows.append({'shift':name,'start':a-timedelta(minutes=before),'end':b+timedelta(minutes=after)})
        day+=timedelta(days=1)
    for r in rows:
        if r.get('shift_start') and get_datetime(r['shift_start']).date()>start.date() and r.get('shift_end'):
            windows.append({'shift':r.get('shift') or '', 'start':r.get('shift_actual_start') or r['shift_start'],
                            'end':r.get('shift_actual_end') or r['shift_end']})
    competing=bool(frappe.get_all('Overtime Authorization',filters=[['employee','=',doc.employee],['docstatus','=',1],
        ['name','!=',doc.name],['authorization_start','<',end],['authorization_end','>',start]],pluck='name',limit=1))
    value=compare_overnight(authorization={'start':start,'end':end,'shift':doc.shift_type},checkins=rows,
        policies=policy_map,next_windows=windows,now=now_datetime(),context_complete=context_complete,competing=competing)
    value['source_hash']=hashlib.sha256(json.dumps({'rows':rows,'policies':policies,'assignments':assignments,
        'default_shift':default,'windows':windows},sort_keys=True,default=str).encode()).hexdigest()
    value.update(available=True,notes=[
        'Se propone una agrupación en memoria: no se modifican tipos IN/OUT, turnos ni banderas de las marcaciones.',
        'La autorización amplía la jornada de origen únicamente para comparar. Las marcas que también caben en el turno siguiente requieren revisión.',
        'Los turnos siguientes consideran asignaciones activas, turno por defecto y ventanas guardadas en las marcaciones; no son una política histórica inmutable.',
        'Last Sync of Checkin es una señal de sincronización, no prueba de que el empleado haya ponchado correctamente.',
        'La propuesta no sustituye los importes ni las horas guardadas y no habilita liquidación automática.',
    ])
    return value
