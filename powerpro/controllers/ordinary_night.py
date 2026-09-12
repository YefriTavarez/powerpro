"""Independent ordinary-night earnings; original punches remain unchanged."""
from datetime import timedelta
from math import isfinite
import frappe
from frappe import _
from frappe.utils import getdate, get_datetime, flt, now_datetime
from powerpro.controllers.overtime import get_schedule_context, _reconciliation_rows
from powerpro.controllers.overtime_pay_policy import get_effective_policy
from powerpro.payroll_rules.ordinary_night import evaluate_night_work, VERSION
from powerpro.payroll_rules.overtime import get_shift_window
from powerpro.payroll_rules.manual_overtime import verification_roles

DT = 'Ordinary Night Settlement'
FINAL = {'Created', 'Payroll Submitted', 'Paid', 'Credited'}


def check_role():
    settings = frappe.get_single('DGII Payroll Settings')
    if not verification_roles(settings.get('overtime_manual_verification_roles')).intersection(frappe.get_roles()):
        frappe.throw(_('Su rol no permite verificar nocturnidad.'), frappe.PermissionError)


def _certified_session(extensions, employee, shift, *, for_update=False):
    """Reuse accepted HR evidence without recursively calling OT/night coverage."""
    from powerpro.controllers.checkin_overtime import _data, _evidence_hash
    from powerpro.controllers.checkin_overtime_review import accept_result
    from powerpro.payroll_rules.overtime_manual_session import evaluate_manual_session
    found=[]
    for extension in extensions:
        auth=frappe.get_doc('Overtime Authorization',extension.name,for_update=for_update)
        if auth.reconciliation_source!='Manual Verification':continue
        saved=frappe.parse_json(auth.evidence_snapshot or '{}')
        review=saved.get('review') or {}
        declaration=review.get('manual_declaration')
        if not declaration:continue
        auth.check_permission('read')
        if not auth.evidence_enrolled or auth.employee!=employee or auth.shift_type!=shift:
            frappe.throw(_('La declaración no corresponde a esta jornada inscrita.'))
        data,_settings=_data(auth,for_update=for_update,include_weekly=False)
        # Weekly financial readiness can change independently. Work, policy,
        # assignment, calendar and original punches must still be the accepted input.
        previous=saved.get('input') or {}
        if (not review.get('reviewed_by') or not review.get('request_token')
                or review.get('input_hash')!=saved.get('input_hash')
                or _evidence_hash(declaration)!=_evidence_hash(previous.get('manual_declaration'))
                or any(_evidence_hash(value)!=_evidence_hash(previous.get(key)) for key,value in data.items() if key!='weekly')):
            frappe.throw(_('La evidencia de la jornada declarada cambió. Gestión Humana debe revisarla antes de liquidar nocturnidad.'))
        current=evaluate_manual_session(declaration=declaration,authorization=data['authorization'],rows=data['rows'],
            contexts=data['contexts'],now=now_datetime(),competing=data['competing'])
        current.update(input_hash=saved['input_hash'],settlement_blockers=[])
        current=accept_result(current,review)
        if current['state']!='Verified' or _evidence_hash(current['worked_intervals'])!=_evidence_hash(saved.get('worked_intervals')):
            frappe.throw(_('La jornada declarada requiere una nueva revisión.'))
        found.append({'authorization':auth.name,'review':review,'worked_intervals':current['worked_intervals']})
    if len(found)>1:
        frappe.throw(_('Hay más de una declaración de jornada completa; unifique su revisión antes de liquidar nocturnidad.'))
    return found[0] if found else None


def build_preview(doc, *, for_update=False):
    from powerpro.controllers.checkin_overtime import _evidence_hash
    from powerpro.controllers.overtime_cash_settlement import _get_hourly_rate
    employee = frappe.get_doc('Employee', doc.employee, for_update=for_update)
    employee.check_permission('read')
    company = frappe.get_doc('Company', employee.company, for_update=for_update)
    day = getdate(doc.work_date)
    assignments = _reconciliation_rows('Shift Assignment', for_update=for_update,
        filters={'employee': employee.name, 'docstatus': 1, 'status': 'Active', 'start_date': ['<=', day+timedelta(days=2)]},
        fields=['name', 'shift_type', 'start_date', 'end_date'], limit=1001)
    if len(assignments)>1000: frappe.throw(_('Demasiadas asignaciones de turno.'))
    def shift_at(date):
        names = {r.shift_type for r in assignments if getdate(r.start_date)<=date and (not r.end_date or getdate(r.end_date)>=date)}
        if not names and employee.default_shift: names={employee.default_shift}
        if len(names)!=1: frappe.throw(_('La fecha requiere un turno asignado inequívoco o un turno por defecto.'))
        return frappe.get_doc('Shift Type', next(iter(names)), for_update=for_update)
    current=shift_at(day)
    holidays=current.get('holiday_list') or employee.get('holiday_list') or company.default_holiday_list
    context=get_schedule_context(day,current.name,holidays,for_update=for_update)
    start,end=get_datetime(context['shift_start']),get_datetime(context['shift_end'])
    extensions=_reconciliation_rows('Overtime Authorization',for_update=for_update,
        filters={'employee':employee.name,'work_date':day,'docstatus':1},
        fields=['name','authorization_start','authorization_end','status','shift_type'],order_by='authorization_start asc',limit=51)
    if len(extensions)>50:frappe.throw(_('Demasiadas prolongaciones para esta jornada.'))
    if any(r.status!='Approved' or r.shift_type!=current.name for r in extensions):
        frappe.throw(_('Las prolongaciones deben estar aprobadas y corresponder al turno resuelto.'))
    windows=[{'name':r.name,'start':str(r.authorization_start),'end':str(r.authorization_end)} for r in extensions]
    lo=min([start]+[get_datetime(r['start']) for r in windows]);hi=max([end]+[get_datetime(r['end']) for r in windows])
    policy=get_effective_policy(frappe._dict(company=company.name,authorization_start=lo,authorization_end=hi),for_update=for_update)
    if not policy:frappe.throw(_('Falta una política aprobada que cubra toda la jornada.'))
    next_windows=[]
    date=day+timedelta(days=1)
    while date<=hi.date():
        nxt=shift_at(date);a,b=get_shift_window(date,nxt.start_time,nxt.end_time)
        next_windows.append({'shift':nxt.name,'start':str(a-timedelta(minutes=flt(nxt.begin_check_in_before_shift_start_time))),
                             'end':str(b+timedelta(minutes=flt(nxt.allow_check_out_after_shift_end_time)))})
        date+=timedelta(days=1)
    shift={k:current.get(k) for k in ['name','start_time','end_time','last_sync_of_checkin','determine_check_in_and_check_out',
        'working_hours_calculation_based_on','begin_check_in_before_shift_start_time','allow_check_out_after_shift_end_time']}
    rows=_reconciliation_rows('Employee Checkin',for_update=for_update,
        filters=[['employee','=',employee.name],['time','>=',lo-timedelta(minutes=flt(current.begin_check_in_before_shift_start_time))],
                 ['time','<=',hi+timedelta(minutes=flt(current.allow_check_out_after_shift_end_time))]],
        fields=['name','time','log_type','shift','shift_start','shift_end','shift_actual_start','shift_actual_end','skip_auto_attendance','offshift'],
        order_by='time asc,name asc',limit=2001)
    if len(rows)>2000:frappe.throw(_('Demasiadas marcaciones para una jornada.'))
    salary_fields=['name','base','from_date','salary_structure']
    if frappe.get_meta('Salary Structure Assignment').has_field('salary_per_hour'):salary_fields.append('salary_per_hour')
    rates=_reconciliation_rows('Salary Structure Assignment',for_update=for_update,
        filters={'employee':employee.name,'company':company.name,'docstatus':1,'from_date':['<=',day]},
        fields=salary_fields,order_by='from_date desc,creation desc',limit=1)
    if not rates:frappe.throw(_('Falta la asignación salarial vigente.'))
    if frappe.db.get_value('Salary Structure',rates[0].salary_structure,'salary_slip_based_on_timesheet'):
        frappe.throw(_('La nómina por hojas de tiempo requiere revisar su nocturnidad para evitar duplicarla.'))
    rate=_get_hourly_rate(rates[0])
    if not isfinite(rate) or rate<=0:frappe.throw(_('La tarifa por hora debe ser positiva y finita.'))
    certified=_certified_session(extensions,employee.name,current.name,for_update=for_update)
    result=evaluate_night_work(rows=[dict(r) for r in rows],shift=shift,context=context,extensions=windows,
                              next_windows=next_windows,now=now_datetime(),basis=policy['night_basis'],
                              certified_intervals=certified['worked_intervals'] if certified else None)
    data={'version':VERSION,'employee':employee.name,'company':company.name,'work_date':str(day),'shift':shift,
          'context':context,'extensions':windows,'next_windows':next_windows,'rows':[dict(r) for r in rows],
          'policy':policy,'rate_basis':dict(rates[0]),'hourly_rate':rate}
    if certified:
        data['certified_session']=certified
        result['reconciliation_source']='Manual Verification'
    result.update(input=data,input_hash=_evidence_hash(data),ordinary_hours=result.get('night_session',{}).get('ordinary_premium_hours',0),
                  hourly_rate=rate,currency=company.default_currency,night_percent=policy['night_percent'])
    result['amount']=round(result['ordinary_hours']*rate*policy['night_percent']/100,2)
    return result


def validate_fresh(doc):
    saved=frappe.parse_json(doc.evidence_snapshot or '{}')
    current=build_preview(doc,for_update=True)
    if current['state']!='Verified' or not saved.get('input_hash') or saved['input_hash']!=current['input_hash']:
        frappe.throw(_('La evidencia nocturna cambió o está incompleta. Revise y guarde de nuevo antes de liquidar.'))
    if current['amount']<=0:frappe.throw(_('No hay recargo nocturno ordinario por liquidar.'))
    return current


def coverage_for_authorization(auth, result, *, for_update=False):
    """A settled ordinary claim must still agree with the OT complete-session evidence."""
    from powerpro.controllers.checkin_overtime import _evidence_hash
    from powerpro.controllers.overtime_cash_settlement import _get_linked_additional_salaries
    rows=_reconciliation_rows(DT,for_update=for_update,filters={'employee':auth.employee,'work_date':auth.work_date,'docstatus':1},pluck='name',limit=2)
    if len(rows)!=1:return None
    doc=frappe.get_doc(DT,rows[0],for_update=for_update)
    saved=frappe.parse_json(doc.evidence_snapshot or '{}');fresh=build_preview(doc,for_update=for_update)
    if fresh['state']!='Verified' or fresh['input_hash']!=saved.get('input_hash'):return None
    if _evidence_hash(fresh['worked_intervals'])!=_evidence_hash(result.get('worked_intervals')):return None
    if abs(flt(fresh['ordinary_hours'])-flt(result['night_session']['ordinary_premium_hours']))>.0001:return None
    if not _get_linked_additional_salaries(doc,docstatus=1,for_update=for_update):return None
    return {'name':doc.name,'input_hash':fresh['input_hash'],'ordinary_hours':fresh['ordinary_hours']}


@frappe.whitelist()
def get_status(name):
    doc=frappe.get_doc(DT,name);doc.check_permission('read')
    current=build_preview(doc)
    saved=frappe.parse_json(doc.evidence_snapshot or '{}')
    return {'state':'Needs Review' if doc.docstatus==1 and current['input_hash']!=saved.get('input_hash') else current['state'],
            'issues':current['issues'],'settlement_status':doc.settlement_status}
