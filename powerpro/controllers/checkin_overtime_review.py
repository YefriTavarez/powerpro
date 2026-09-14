"""Explicit HR acceptance of corrected checkin evidence, with atomic replacement."""
import hashlib
from copy import deepcopy
from datetime import timedelta
import frappe
from frappe import _
from frappe.utils import getdate, flt, cint, now_datetime
from powerpro.controllers import checkin_overtime as evidence
from powerpro.controllers.overtime import _reconciliation_rows
from powerpro.controllers.overtime_source import AUTH,RETRO,evidence_enabled,links

APPLIED = 'HR Evidence Review Applied'
REVIEWABLE = {'worked_authorized_mismatch'}


def accept_result(result, review):
    """A reason may accept a measured shortfall, never missing evidence or extra time."""
    if not review or review.get('input_hash') != result['input_hash']:
        return result
    if not result.get('snapshot') or flt(result['snapshot'].get('verified_hours'))<=0:
        frappe.throw(_('Se requiere evidencia de intervalos trabajados antes de aceptar la revisión.'))
    codes={i['code'] for i in result['issues'] if i.get('severity')!='information'}
    # A separately authorized historical interval can be accepted without
    # discarding its early/late physical work or paying that excluded time.
    from powerpro.payroll_rules.overtime_manual_session import authorized_interval_scope
    scoped=bool(result.get('authorized_interval_review')) and authorized_interval_scope(
        result.get('manual_declaration'),'Retroactive Overtime Adjustment')
    if codes-REVIEWABLE or (flt(result['calculation'].get('unapproved_hours'))>0 and not scoped):
        frappe.throw(_('Corrija las marcaciones faltantes o ambiguas y revise el tiempo no autorizado antes de aceptar.'))
    if result['state'] not in {'Verified','Needs Review'}:
        frappe.throw(_('La ventana y la sincronización deben estar completas.'))
    result=deepcopy(result)
    for issue in result['issues']:
        if issue['code'] in REVIEWABLE:
            issue.update(severity='information',accepted_by_hr=True)
    result['state']='Verified';result['review']=review
    result['settlement_ready']=not bool(result['settlement_blockers'])
    return result


def _access(doc,manual_declaration=None):
    evidence._access(doc)
    if not evidence_enabled(doc):
        frappe.throw(_('La autorización no está inscrita en el modo por marcaciones.'))
    if doc.doctype==RETRO:
        doc.check_permission('submit')
        if doc.approver!=frappe.session.user:
            frappe.throw(_('Solo el aprobador asignado puede revisar este ajuste.'),frappe.PermissionError)
    previous_review=frappe.parse_json(doc.evidence_snapshot or '{}').get('review') or {}
    if doc.reconciliation_source in {'Manual Verification','HR Exception','Presumed Attendance'} and not (doc.reconciliation_source=='Manual Verification' and previous_review.get('manual_declaration')):
        frappe.throw(_('Esta revisión conserva marcaciones como fuente; la verificación manual requiere su revisión específica.'))
    if not cint(evidence._settings().get('enable_checkin_overtime_reconciliation')):
        frappe.throw(_('La conciliación por marcaciones está desactivada.'))


def _dependencies(doc, *, for_update=False):
    day=getdate(doc.work_date)
    saved=frappe.parse_json(doc.get('evidence_snapshot') or '{}')
    context=next((r for r in saved.get('input',{}).get('contexts',[]) if r.get('date')==str(day)),{})
    end=max(day,getdate(doc.authorization_end),getdate(context.get('shift_end') or doc.authorization_end))
    last=end+timedelta(days=6-end.weekday())
    found=[]
    for dt in ['Overtime Authorization','Retroactive Overtime Adjustment']:
        rows=_reconciliation_rows(dt,for_update=for_update,filters=[['employee','=',doc.employee],['docstatus','=',1],
            ['work_date','between',[day,last]],['authorization_start','>',doc.authorization_start],['verified_hours','>',0]],
            fields=['name','settlement_status','regular_35_hours','regular_100_hours'],order_by='authorization_start asc',limit=201)
        if len(rows)>200:frappe.throw(_('Demasiadas dependencias semanales; acote la revisión.'))
        for row in rows:
            if flt(row.regular_35_hours)+flt(row.regular_100_hours)>0:
                found.append({'doctype':dt,'name':row.name,'settlement_status':row.settlement_status,
                              'blocks_reversal':row.settlement_status in evidence.FINAL})
    return found


def _financial(doc):
    keys=['settlement_status','holiday_cash_status','settlement_method','settlement_references','settlement_amount','settlement_breakdown',
          'settlement_salary_slip','compensatory_credit','leave_allocation']
    return {key:doc.get(key) for key in keys}


def _preview(doc, reason, *, for_update=False,manual_declaration=None):
    if not isinstance(reason,str) or not 1<=len(reason.strip())<=2000:
        frappe.throw(_('Indique un motivo de revisión de 1 a 2000 caracteres.'))
    if isinstance(manual_declaration,str):manual_declaration=frappe.parse_json(manual_declaration)
    if manual_declaration is not None and not cint(evidence._settings().get('enable_manual_overtime_verification')):
        frappe.throw(_('La verificación manual está desactivada.'))
    raw=evidence.build_result(doc,for_update=for_update,use_saved_review=False,manual_declaration=manual_declaration)
    accepted=accept_result(raw,{'input_hash':raw['input_hash'],'reason':reason.strip()})
    frozen=frappe.parse_json(doc.evidence_snapshot or '{}')
    if frozen.get('input_hash')==raw['input_hash'] and (raw['state']=='Verified' or frozen.get('review')):
        frappe.throw(_('La evidencia no cambió y ya fue validada. No se requiere sustituir la liquidación.'))
    from powerpro.controllers.overtime_rest import get_election
    election=get_election(doc,for_update=for_update)
    if election:
        accepted['settlement_blockers'].append('La elección anterior se cancelará; el empleado debe confirmar la elección sobre las horas revisadas.')
        accepted['settlement_ready']=False
    estimate=None
    if accepted['settlement_ready'] and doc.planned_settlement=='Cash':
        from powerpro.payroll_rules.overtime_cash_settlement import calculate_cash_settlement
        from powerpro.payroll_rules.overtime_pay_policy import rates
        p=accepted['input']['pay_policy'];calculation=accepted['calculation']
        from powerpro.payroll_rules.overtime_combined_day import cash_kwargs
        estimate=calculate_cash_settlement(hourly_rate=accepted['input']['rate_basis']['hourly_rate'],
            **{key:calculation.get(key,0) for key in ['regular_35_hours','regular_100_hours','holiday_100_hours','weekly_rest_hours','night_hours']},
            **rates(p),holiday_base_covered_hours=calculation.get('holiday_base_covered_hours',0),
            **cash_kwargs(p,calculation),
            weekly_rest_overtime_percent=p['weekly_rest_percent'] if p.get('weekly_rest_cash') else None)['total_amount']
    dependencies=_dependencies(doc,for_update=for_update)
    payload={**links(doc),'reason':reason.strip(),'before':frozen,'financial_before':_financial(doc),
             'after':accepted,'dependencies':dependencies,'proposed_amount':estimate}
    # Evaluation timestamps/watermarks are not changes in work evidence.
    stable={**links(doc),'reason':reason.strip(),'before':evidence._evidence_hash(frozen),
            'financial_before':_financial(doc),'new_hash':raw['input_hash'],'dependencies':dependencies,
            'settlement_ready':accepted['settlement_ready'],'settlement_blockers':accepted['settlement_blockers']}
    payload['token']=hashlib.sha256(evidence._json(stable).encode()).hexdigest()
    return payload


@frappe.whitelist()
def preview_review(authorization, reason, manual_declaration=None, source_type=AUTH):
    if source_type not in {AUTH,RETRO}:frappe.throw(_('Origen de revisión no admitido.'))
    doc=frappe.get_doc(source_type,authorization);_access(doc)
    if doc.docstatus!=1 or doc.status!='Approved':frappe.throw(_('La autorización debe permanecer aprobada.'))
    result=_preview(doc,reason,manual_declaration=manual_declaration)
    from powerpro.payroll_rules.overtime_pay_policy import review_summary
    return {'token':result['token'],**links(doc),'reason':result['reason'],
            'before':result['before'].get('snapshot',{}),'after':result['after']['snapshot'],
            'financial_before':result['financial_before'],'dependencies':result['dependencies'],
            'proposed_amount':result['proposed_amount'],'manual_declaration':result['after'].get('manual_declaration'),
            'checkin_comparison':result['after'].get('checkin_comparison'),
            'rules_summary':review_summary(result['after']),
            'settlement_ready':result['after']['settlement_ready'],
            'settlement_blockers':result['after']['settlement_blockers']}


@frappe.whitelist(methods=['POST'])
def apply_review(authorization, reason, token, manual_declaration=None, source_type=AUTH):
    from powerpro.controllers.overtime_rest import _lock_source
    doc,call=_lock_source(authorization,source_type=source_type);_access(doc)
    existing=frappe.db.get_value('Overtime Reconciliation Run',{**links(doc),'result_status':APPLIED,'evidence_hash':token},'name',for_update=True)
    if existing:return {'status':'Applied','audit':existing,'idempotent':True}
    preview=_preview(doc,reason,for_update=True,manual_declaration=manual_declaration)
    if not token or preview['token']!=token:
        frappe.throw(_('La evidencia o la liquidación cambió. Revise una vista previa nueva.'))
    blocked=[r for r in preview['dependencies'] if r['blocks_reversal']]
    if blocked:
        frappe.throw(_('Revise primero las liquidaciones semanales dependientes: {0}.').format(', '.join(r['name'] for r in blocked)))
    frappe.db.savepoint('checkin_hr_review')
    try:
        from powerpro.controllers.automatic_overtime import _reverse_outputs
        from powerpro.controllers.overtime_rest import release_for_source
        _reverse_outputs(doc,frappe._dict(name=token[:12],reason=preview['reason']))
        release_for_source(doc)
        result=preview['after']
        review={'input_hash':result['input_hash'],'reason':preview['reason'],'reviewed_by':frappe.session.user,
                'reviewed_on':str(now_datetime()),'request_token':token}
        declaration=result.get('manual_declaration')
        if declaration is not None:review['manual_declaration']=declaration
        result['review']=review
        # Re-evaluate employee choice after reversing the previous obligation.
        values={**result['snapshot'],'reconciliation_source':'Manual Verification' if declaration is not None else 'Employee Checkin','reconciled_by':frappe.session.user,
            'reconciled_on':now_datetime(),'evidence_snapshot':evidence._json(result),'evidence_last_hash':result['input_hash'],
            'evidence_status':'Verified','evidence_settlement_ready':0,'evidence_retry_after':now_datetime(),
            'source_checkins':evidence._json(result['source_checkins']),
            'reconciliation_intervals':evidence._json(result['calculation']['intervals']),
            'unapproved_intervals':evidence._json(result['calculation']['unapproved_intervals']),
            'reconciliation_warnings':evidence._json(result['issues']),
            'settlement_status':'Pending','holiday_cash_status':None,'settlement_method':None,'settlement_amount':0,
            'settlement_references':None,'settlement_breakdown':None,'settlement_salary_slip':None,
            'compensatory_credit':None,'leave_allocation':None,'compensatory_hours':0,'compensatory_days':0,'compensatory_residual_hours':0}
        values.update(manual_worked_intervals=evidence._json(declaration['intervals']) if declaration else None,
            manual_verification_reason=preview['reason'] if declaration else None,
            manual_checkin_comparison=evidence._json(result.get('checkin_comparison')) if declaration else None)
        if doc.doctype==RETRO:
            # Scheduling and manual display fields only exist on authorizations;
            # historical evidence and declaration are retained in the audit JSON.
            values={key:value for key,value in values.items() if doc.meta.has_field(key)}
        doc.db_set(values)
        fresh=evidence.build_result(doc,for_update=True)
        values={'evidence_snapshot':evidence._json(fresh),'evidence_settlement_ready':int(fresh['settlement_ready'])}
        if doc.doctype==AUTH:values['evidence_issues']=evidence._json(fresh['issues']+[{'code':'settlement_pending','message':m} for m in fresh['settlement_blockers']])
        doc.db_set(values)
        if fresh['settlement_ready'] and (doc.get('evidence_auto_settle') or preview['financial_before']['settlement_status'] in evidence.FINAL):
            if doc.doctype==RETRO:
                from powerpro.controllers.retroactive_evidence import settle_reviewed_cash
                settle_reviewed_cash(doc,fresh)
            else:
                from powerpro.controllers.overtime_settlement import _settle_authorization
                _settle_authorization(doc,payroll_date=doc.auto_payroll_date,settings=evidence._settings())
                doc.db_set({'evidence_status':'Frozen','evidence_retry_after':None})
        evidence._sync(call)
        doc.reload()
        evidence._audit(doc,{'state':APPLIED,'input_hash':token,'issues':[],
            'review':review,'before':preview['before'],'after':fresh,
            'financial_before':preview['financial_before'],'financial_after':_financial(doc),'dependencies':preview['dependencies']})
    except Exception:
        frappe.db.rollback(save_point='checkin_hr_review')
        raise
    audit=frappe.db.get_value('Overtime Reconciliation Run',{**links(doc),'result_status':APPLIED,'evidence_hash':token},'name',for_update=True)
    return {'status':'Applied','audit':audit,'settlement_status':doc.settlement_status,'settlement_ready':bool(doc.evidence_settlement_ready)}
