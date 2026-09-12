import frappe
from frappe import _
from frappe.utils import cint, getdate
from datetime import datetime, time, timedelta
from powerpro.controllers.overtime_rest import DT,get_rest_status
from powerpro.controllers.overtime_source import identity


def execute(filters=None):
    filters=frappe._dict(filters or {})
    query={'docstatus':1,'choice':'Compensatory Rest'}
    if filters.get('company'):query['company']=filters.company
    if filters.get('employee'):query['employee']=filters.employee
    date_filters=[]
    if filters.get('from_date'):
        date_filters.append(['planned_end','>=',datetime.combine(getdate(filters.from_date),time.min)])
    if filters.get('to_date'):
        date_filters.append(['planned_end','<',datetime.combine(getdate(filters.to_date)+timedelta(days=1),time.min)])
    if filters.get('from_date') and filters.get('to_date') and getdate(filters.from_date)>getdate(filters.to_date):
        frappe.throw(_('La fecha inicial no puede ser posterior a la final.'))
    query_filters=[[field,'=',value] for field,value in query.items()]+date_filters
    rows=frappe.get_list(DT,filters=query_filters,fields=['name','authorization','retroactive_adjustment','employee','planned_start','planned_end','leave_application'],
                         order_by='planned_end asc, name asc',limit_page_length=201)
    data=[];restricted=False
    labels={'Approved':'Pendiente de crédito','Credited':'Pendiente de licencia','Scheduled':'Programado',
            'Enjoyed':'Disfrutado','Overdue':'Vencido: revisar disfrute','Review':'Revisión de evidencia y respaldo'}
    for row in rows[:200]:
        source_type,source=identity(row)
        if not frappe.has_permission(source_type,'read',doc=source):
            restricted=True;continue
        try:status=get_rest_status(row.name)
        except frappe.PermissionError:
            restricted=True;continue
        if status['status']=='Enjoyed' and not cint(filters.get('include_enjoyed')):continue
        data.append({**row,'status':labels.get(status['status'],status['status']),'credit':status['credit']})
    columns=[{'fieldname':f,'label':_(label),'fieldtype':kind,'options':options,'width':width} for f,label,kind,options,width in [
        ('name','Elección','Link',DT,180),('employee','Empleado','Link','Employee',200),
        ('authorization','Autorización','Link','Overtime Authorization',180),('retroactive_adjustment','Ajuste retroactivo','Link','Retroactive Overtime Adjustment',180),('status','Seguimiento','Data',None,240),
        ('planned_start','Inicio','Datetime',None,170),('planned_end','Fin','Datetime',None,170),
        ('leave_application','Licencia','Link','Leave Application',180),('credit','Crédito','Link','Overtime Compensatory Credit',180)]]
    message=_('La consulta supera 200 elecciones. Este resultado es parcial: acote las fechas, empresa o empleado para revisar el resto.') if len(rows)>200 else None
    if restricted:message=(message+' ' if message else '')+_('Se omitieron elecciones cuyo respaldo no es accesible para este usuario.')
    return columns,data,message
