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
from powerpro.controllers.overtime_document_locks import lock_employees_before_save, check_locked_employee

DT = 'Ordinary Night Settlement'
FINAL = {'Created', 'Payroll Submitted', 'Paid', 'Credited'}
COVERAGE_PENDING = 'La jornada contiene recargo nocturno fuera de la autorización; complete su liquidación ordinaria independiente.'


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
        auth=frappe.get_doc(extension.get('source_type') or 'Overtime Authorization',extension.name,for_update=for_update)
        if auth.reconciliation_source!='Manual Verification':continue
        saved=frappe.parse_json(auth.evidence_snapshot or '{}')
        review=saved.get('review') or {}
        declaration=review.get('manual_declaration')
        if not declaration:continue
        auth.check_permission('read')
        from powerpro.controllers.overtime_source import evidence_enabled,links
        if not evidence_enabled(auth) or auth.employee!=employee or auth.shift_type!=shift:
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
        found.append({**links(auth),'review':review,'worked_intervals':current['worked_intervals']})
    if len(found)>1:
        frappe.throw(_('Hay más de una declaración de jornada completa; unifique su revisión antes de liquidar nocturnidad.'))
    return found[0] if found else None


def build_preview(doc, *, for_update=False, historical_snapshot=None, historical_declaration=None):
    from powerpro.controllers.checkin_overtime import _evidence_hash
    from powerpro.controllers.overtime_cash_settlement import _get_hourly_rate
    physical_only=historical_snapshot is not None
    if physical_only and doc.docstatus!=2:
        frappe.throw(_('La evaluación histórica requiere una liquidación cancelada.'))
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
    historical=_reconciliation_rows('Retroactive Overtime Adjustment',for_update=for_update,
        filters={'employee':employee.name,'work_date':day,'docstatus':1,'reconciliation_engine':'Verified Checkins'},
        fields=['name','authorization_start','authorization_end','status','shift_type'],order_by='authorization_start asc',limit=51)
    for row in historical:row['source_type']='Retroactive Overtime Adjustment'
    extensions.extend(historical)
    if physical_only:
        # Financial cancellation does not shorten the documented old session.
        # New replacements are not silently added to its historical window.
        from powerpro.controllers.ordinary_night_history import historical_extensions
        extensions=historical_extensions(doc,historical_snapshot,for_update=for_update)
    extensions.sort(key=lambda row:(get_datetime(row.authorization_start),row.get('source_type') or 'Overtime Authorization',row.name))
    if len(extensions)>50:frappe.throw(_('Demasiadas prolongaciones para esta jornada.'))
    if any((r.status!='Approved' and not (physical_only and r.docstatus==2)) or r.shift_type!=current.name for r in extensions):
        frappe.throw(_('Las prolongaciones deben estar aprobadas y corresponder al turno resuelto.'))
    windows=[{'name':r.name,'start':str(r.authorization_start),'end':str(r.authorization_end),
              **({'source_type':r.source_type} if r.get('source_type') else {})} for r in extensions]
    lo=min([start]+[get_datetime(r['start']) for r in windows]);hi=max([end]+[get_datetime(r['end']) for r in windows])
    policy=None
    if not physical_only:
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
    if physical_only:
        from powerpro.controllers.ordinary_night_history import evaluate_physical
        return evaluate_physical(doc,company.name,rows,shift,context,windows,next_windows,historical_declaration)
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
    saved=frappe.parse_json(doc.evidence_snapshot or '{}')
    try:fresh=build_preview(doc,for_update=for_update)
    except frappe.ValidationError:
        # Stale ordinary coverage is an explicit financial blocker. It must not
        # prevent HR from recording corrected work and reversing the old OT.
        return None
    if fresh['state']!='Verified' or fresh['input_hash']!=saved.get('input_hash'):return None
    if _evidence_hash(fresh['worked_intervals'])!=_evidence_hash(result.get('worked_intervals')):return None
    if abs(flt(fresh['ordinary_hours'])-flt(result['night_session']['ordinary_premium_hours']))>.0001:return None
    if not _get_linked_additional_salaries(doc,docstatus=1,for_update=for_update):return None
    return {'name':doc.name,'input_hash':fresh['input_hash'],'ordinary_hours':fresh['ordinary_hours']}


def automatic_coverage_allowed(auth, result):
    """Operational opt-in stays outside the frozen mathematical policy snapshot."""
    from frappe.utils import cint
    policy=(result.get('input') or {}).get('pay_policy') or {}
    return bool(auth.evidence_enrolled and auth.evidence_auto_settle and result['state']=='Verified'
        and result.get('night_session',{}).get('ordinary_premium_hours')
        and not result.get('ordinary_night_settlement')
        and result.get('settlement_blockers')==[COVERAGE_PENDING]
        and policy.get('name') and cint(frappe.db.get_value('Overtime Pay Policy',
            {'name':policy['name'],'docstatus':1},'auto_ordinary_night')))


def create_automatic_coverage(auth, result):
    """Caller owns Call->Employee->Authorization locks and a financial savepoint."""
    from powerpro.controllers.checkin_overtime import _evidence_hash
    if not automatic_coverage_allowed(auth,result):
        frappe.throw(_('La política y la autorización no habilitan esta liquidación nocturna automática.'))
    saved=frappe.parse_json(auth.evidence_snapshot or '{}')
    if not saved.get('input_hash') or saved['input_hash']!=result.get('input_hash'):
        frappe.throw(_('Guarde primero la evidencia verificada de la autorización.'))
    existing=_reconciliation_rows(DT,for_update=True,
        filters={'employee':auth.employee,'work_date':auth.work_date,'docstatus':['<',2]},
        fields=['name','docstatus'],limit=2)
    if existing:
        frappe.throw(_('Ya existe una liquidación nocturna para revisar o reutilizar: {0}.').format(', '.join(r.name for r in existing)))
    if not auth.auto_payroll_date:
        frappe.throw(_('Falta la fecha de nómina del recargo nocturno ordinario.'))
    doc=frappe.get_doc({'doctype':DT,'employee':auth.employee,'work_date':auth.work_date,
        'settlement_payroll_date':auth.auto_payroll_date,
        'review_reference':_('Automática desde {0}; política {1}; evidencia {2}.').format(
            auth.name,result['input']['pay_policy']['name'],result['input_hash'])})
    preview=build_preview(doc,for_update=True)
    if (preview['state']!='Verified' or preview['amount']<=0
            or _evidence_hash(preview['worked_intervals'])!=_evidence_hash(result.get('worked_intervals'))
            or abs(flt(preview['ordinary_hours'])-flt(result['night_session']['ordinary_premium_hours']))>.0001
            or preview['input']['policy']['name']!=result['input']['pay_policy']['name']):
        frappe.throw(_('La evidencia nocturna no coincide con la jornada verificada de la autorización.'))
    doc.insert();doc.submit()
    return doc


@frappe.whitelist()
def get_status(name):
    doc=frappe.get_doc(DT,name);doc.check_permission('read')
    if doc.docstatus==2:
        from powerpro.controllers.ordinary_night_history import get_status as historical_status
        return historical_status(name)
    current=build_preview(doc)
    saved=frappe.parse_json(doc.evidence_snapshot or '{}')
    return {'state':'Needs Review' if doc.docstatus==1 and current['input_hash']!=saved.get('input_hash') else current['state'],
            'issues':current['issues'],'settlement_status':doc.settlement_status}
