"""Bounded, internal weekly evidence loader for the enrolled reconciliation service."""
from datetime import datetime,time,timedelta

import frappe
from frappe.utils import get_datetime,getdate
from powerpro.controllers.overtime import _reconciliation_rows,get_schedule_context

POLICY_FIELDS=('name','start_time','end_time','last_sync_of_checkin',
               'determine_check_in_and_check_out','working_hours_calculation_based_on',
               'begin_check_in_before_shift_start_time','allow_check_out_after_shift_end_time')


def load_week(doc,employee,assignments,*,for_update=False):
    end=get_datetime(doc.authorization_end)
    day=get_datetime(doc.authorization_start).date()
    first=day-timedelta(days=day.weekday())
    start=datetime.combine(first,time.min)
    rows=_reconciliation_rows('Employee Checkin',for_update=for_update,
        filters=[['employee','=',doc.employee],['time','>=',start-timedelta(days=1)],['time','<=',end]],
        fields=['name','time','log_type','shift','shift_start','shift_end','shift_actual_start','shift_actual_end',
                'skip_auto_attendance','offshift'],order_by='time asc, name asc',limit=4001)
    if len(rows)>4000:raise ValueError('La semana supera el límite de marcaciones; requiere revisión.')
    attendances=_reconciliation_rows('Attendance',for_update=for_update,
        filters={'employee':doc.employee,'docstatus':1,'attendance_date':['between',[first-timedelta(days=1),end.date()]]},
        fields=['name','attendance_date','status','docstatus','shift'],order_by='attendance_date asc, name asc',limit=101)
    if len(attendances)>100:raise ValueError('La semana supera el límite de asistencias; requiere revisión.')
    shifts={};policies={};schedules=[];issues=[]
    def shift(name):
        if name not in shifts:
            shifts[name]=frappe.get_doc('Shift Type',name,for_update=for_update)
            policies[name]={k:shifts[name].get(k) for k in POLICY_FIELDS}
        return shifts[name]
    for row in rows:
        if row.get('shift'):shift(row.shift)
    company=frappe.get_doc('Company',employee.company,for_update=for_update)
    day=first-timedelta(days=1)
    while day<=end.date():
        names={a.shift_type for a in assignments if getdate(a.start_date)<=day and (not a.end_date or getdate(a.end_date)>=day)}
        if not names and employee.get('default_shift'):names={employee.default_shift}
        if len(names)!=1:
            issues.append({'code':'weekly_shift_ambiguous' if names else 'weekly_shift_missing','date':str(day)})
        for name in sorted(names):
            current=shift(name)
            holidays=current.get('holiday_list') or employee.get('holiday_list') or company.get('default_holiday_list')
            context=get_schedule_context(day,name,holidays,for_update=for_update)
            context.update(date=str(day),shift=name)
            schedules.append(context)
        day+=timedelta(days=1)
    return {'start':start,'cutoff':end,'rows':[dict(r) for r in rows],
            'policies':policies,'schedules':schedules,'attendances':[dict(r) for r in attendances],
            'context_issues':issues}
