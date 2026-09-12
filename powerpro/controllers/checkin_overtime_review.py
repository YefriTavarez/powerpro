"""Explicit HR acceptance of corrected checkin evidence, with atomic replacement."""
import hashlib
from copy import deepcopy
from datetime import timedelta
import frappe
from frappe import _
from frappe.utils import getdate, flt, cint, now_datetime
from powerpro.controllers import checkin_overtime as evidence
from powerpro.controllers.overtime import _reconciliation_rows

APPLIED = 'HR Evidence Review Applied'
REVIEWABLE = {'worked_authorized_mismatch'}


def accept_result(result, review):
    """A reason may accept a measured shortfall, never missing evidence or extra time."""
    if not review or review.get('input_hash') != result['input_hash']:
        return result
    if not result.get('snapshot') or flt(result['snapshot'].get('verified_hours'))<=0:
        frappe.throw(_('Se requiere evidencia de intervalos trabajados antes de aceptar la revisión.'))
    codes={i['code'] for i in result['issues'] if i.get('severity')!='information'}
    if codes-REVIEWABLE or flt(result['calculation'].get('unapproved_hours'))>0:
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


def _access(doc):
    evidence._access(doc)
    if not doc.get('evidence_enrolled'):
        frappe.throw(_('La autorización no está inscrita en el modo por marcaciones.'))
    if doc.reconciliation_source in {'Manual Verification','HR Exception','Presumed Attendance'}:
        frappe.throw(_('Esta revisión conserva marcaciones como fuente; la verificación manual requiere su revisión específica.'))
    if not cint(evidence._settings().get('enable_checkin_overtime_reconciliation')):
        frappe.throw(_('La conciliación por marcaciones está desactivada.'))


def _dependencies(doc, *, for_update=False):
    day=getdate(doc.work_date);last=day+timedelta(days=6-day.weekday())
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
    keys=['settlement_status','settlement_method','settlement_references','settlement_amount','settlement_breakdown',
          'settlement_salary_slip','compensatory_credit','leave_allocation']
    return {key:doc.get(key) for key in keys}


def _preview(doc, reason, *, for_update=False):
    if not isinstance(reason,str) or not 1<=len(reason.strip())<=2000:
        frappe.throw(_('Indique un motivo de revisión de 1 a 2000 caracteres.'))
    raw=evidence.build_result(doc,for_update=for_update,use_saved_review=False)
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
        estimate=calculate_cash_settlement(hourly_rate=accepted['input']['rate_basis']['hourly_rate'],
            **{key:calculation.get(key,0) for key in ['regular_35_hours','regular_100_hours','holiday_100_hours','weekly_rest_hours','night_hours']},
            **rates(p),weekly_rest_overtime_percent=p['weekly_rest_percent'] if p.get('weekly_rest_cash') else None)['total_amount']
    dependencies=_dependencies(doc,for_update=for_update)
    payload={'authorization':doc.name,'reason':reason.strip(),'before':frozen,'financial_before':_financial(doc),
             'after':accepted,'dependencies':dependencies,'proposed_amount':estimate}
    # Evaluation timestamps/watermarks are not changes in work evidence.
    stable={'authorization':doc.name,'reason':reason.strip(),'before':evidence._evidence_hash(frozen),
            'financial_before':_financial(doc),'new_hash':raw['input_hash'],'dependencies':dependencies,
            'settlement_ready':accepted['settlement_ready'],'settlement_blockers':accepted['settlement_blockers']}
    payload['token']=hashlib.sha256(evidence._json(stable).encode()).hexdigest()
    return payload


@frappe.whitelist()
def preview_review(authorization, reason):
    doc=frappe.get_doc(evidence.AUTH,authorization);_access(doc)
    if doc.docstatus!=1 or doc.status!='Approved':frappe.throw(_('La autorización debe permanecer aprobada.'))
    result=_preview(doc,reason)
    return {'token':result['token'],'authorization':doc.name,'reason':result['reason'],
            'before':result['before'].get('snapshot',{}),'after':result['after']['snapshot'],
            'financial_before':result['financial_before'],'dependencies':result['dependencies'],
            'proposed_amount':result['proposed_amount'],
            'settlement_ready':result['after']['settlement_ready'],
            'settlement_blockers':result['after']['settlement_blockers']}


@frappe.whitelist(methods=['POST'])
def apply_review(authorization, reason, token):
    doc,call=evidence._lock(authorization);_access(doc)
    existing=frappe.db.get_value('Overtime Reconciliation Run',{'authorization':doc.name,'result_status':APPLIED,'evidence_hash':token},'name',for_update=True)
    if existing:return {'status':'Applied','audit':existing,'idempotent':True}
    preview=_preview(doc,reason,for_update=True)
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
        result['review']=review
        # Re-evaluate employee choice after reversing the previous obligation.
        values={**result['snapshot'],'reconciliation_source':'Employee Checkin','reconciled_by':frappe.session.user,
            'reconciled_on':now_datetime(),'evidence_snapshot':evidence._json(result),'evidence_last_hash':result['input_hash'],
            'evidence_status':'Verified','evidence_settlement_ready':0,'evidence_retry_after':now_datetime(),
            'source_checkins':evidence._json(result['source_checkins']),
            'reconciliation_intervals':evidence._json(result['calculation']['intervals']),
            'unapproved_intervals':evidence._json(result['calculation']['unapproved_intervals']),
            'reconciliation_warnings':evidence._json(result['issues']),
            'settlement_status':'Pending','settlement_method':None,'settlement_amount':0,
            'settlement_references':None,'settlement_breakdown':None,'settlement_salary_slip':None,
            'compensatory_credit':None,'leave_allocation':None,'compensatory_hours':0,'compensatory_days':0,'compensatory_residual_hours':0}
        doc.db_set(values)
        fresh=evidence.build_result(doc,for_update=True)
        doc.db_set({'evidence_snapshot':evidence._json(fresh),'evidence_settlement_ready':int(fresh['settlement_ready']),
                    'evidence_issues':evidence._json(fresh['issues']+[{'code':'settlement_pending','message':m} for m in fresh['settlement_blockers']])})
        if fresh['settlement_ready'] and (doc.evidence_auto_settle or preview['financial_before']['settlement_status'] in evidence.FINAL):
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
    audit=frappe.db.get_value('Overtime Reconciliation Run',{'authorization':doc.name,'result_status':APPLIED,'evidence_hash':token},'name',for_update=True)
    return {'status':'Applied','audit':audit,'settlement_status':doc.settlement_status,'settlement_ready':bool(doc.evidence_settlement_ready)}
