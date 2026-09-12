import frappe
from frappe import _
from frappe.utils import cint,getdate
from powerpro.controllers.overtime_evidence_monitor import DT,watch_permission


def execute(filters=None):
    filters=frappe._dict(filters or {})
    query=[]
    if not cint(filters.get('include_current')):query.append(['status','!=','Current'])
    for field in ['company','employee','responsible','source_type']:
        if filters.get(field):query.append([field,'=',filters[field]])
    if filters.get('from_date'):query.append(['work_date','>=',getdate(filters.from_date)])
    if filters.get('to_date'):query.append(['work_date','<=',getdate(filters.to_date)])
    if filters.get('from_date') and filters.get('to_date') and getdate(filters.from_date)>getdate(filters.to_date):
        frappe.throw(_('La fecha inicial no puede ser posterior a la final.'))
    rows=frappe.get_list(DT,filters=query,fields=['name','source_type','source_name','employee','work_date','status',
        'summary','responsible','stored_hours','current_hours','checked_on'],order_by='changed_on desc, name asc',limit_page_length=201)
    data=[]
    labels={'Current':'Vigente','Waiting':'Pendiente','Needs Review':'Requiere revisión','Error':'Error de comprobación'}
    for row in rows[:200]:
        if not watch_permission(row):continue
        row['status']=labels[row.status];data.append(row)
    columns=[{'fieldname':field,'label':_(label),'fieldtype':kind,'options':options,'width':width} for field,label,kind,options,width in [
        ('name','Seguimiento','Link',DT,140),('source_type','Tipo de origen','Link','DocType',180),
        ('source_name','Origen','Dynamic Link','source_type',180),('employee','Empleado','Link','Employee',190),
        ('work_date','Fecha','Date',None,100),('status','Estado','Data',None,160),
        ('stored_hours','Horas guardadas','Float',None,120),('current_hours','Horas actuales','Float',None,120),
        ('responsible','Responsable','Link','User',180),('summary','Resultado','Data',None,300),('checked_on','Comprobado','Datetime',None,170)]]
    message=_('Resultado parcial de 200 registros; acote los filtros.') if len(rows)>200 else None
    return columns,data,message
