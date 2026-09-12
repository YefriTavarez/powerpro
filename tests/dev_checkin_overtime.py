"""DEV-only integration acceptance. Real documents and writes, all rolled back.
Run via bench env from sites. Never execute against production.
"""
import json,uuid
from unittest.mock import patch
import frappe
from frappe.utils import get_datetime
SITE='igcaribe.fortabs.com'
frappe.init(site=SITE);frappe.connect();frappe.set_user('Administrator')
assert frappe.local.site==SITE and frappe.conf.developer_mode
from powerpro.controllers import checkin_overtime as evidence
from powerpro.controllers.overtime_settlement import _validate_ready
prefix='EVIDENCE-DEV-'+uuid.uuid4().hex[:10]
counts=['Employee','Shift Type','Employee Checkin','Overtime Authorization','Overtime Work Call','Overtime Reconciliation Run','Additional Salary','Leave Allocation','Salary Slip','Overtime Pay Policy','Salary Structure Assignment']
before={d:frappe.db.count(d) for d in counts}
original_settings=frappe.db.get_singles_dict('DGII Payroll Settings')
commit,sendmail,enqueue=frappe.db.commit,frappe.sendmail,frappe.enqueue
checks=[]
def forbidden(*args,**kw):raise AssertionError('Outbound or commit attempted in rollback fixture')
frappe.db.commit=forbidden;frappe.sendmail=forbidden;frappe.enqueue=forbidden
try:
 frappe.db.set_single_value('DGII Payroll Settings',{'enable_checkin_overtime_reconciliation':1,'checkin_overtime_effective_from':'2026-09-01'})
 base=frappe.get_doc('Overtime Authorization','AUT-HE-2026-00018')
 employee=frappe.copy_doc(frappe.get_doc('Employee',base.employee));employee.name=prefix+'-EMP';employee.docstatus=0
 employee.employee_name='DEV Evidence';employee.user_id=None;employee.company_email=None;employee.personal_email=None;employee.status='Active'
 shift=frappe.copy_doc(frappe.get_doc('Shift Type','Diurna Extendida'));shift.name=prefix+'-SHIFT';shift.docstatus=0;shift.enable_auto_attendance=0
 shift.determine_check_in_and_check_out='Alternating entries as IN and OUT during the same shift';shift.working_hours_calculation_based_on='Every Valid Check-in and Check-out'
 shift.last_sync_of_checkin='2026-09-16 08:00:00';shift.db_insert()
 employee.default_shift=shift.name;employee.db_insert()
 call=frappe.copy_doc(frappe.get_doc('Overtime Work Call','CONV-HE-2026-00004-1'))
 call.name=None;call.docstatus=0;call.company=employee.company;call.from_date='2026-09-15';call.to_date='2026-09-15';call.planned_settlement='Cash'
 call.automation_mode='Verified Checkins';call.evidence_auto_settle=0
 call.set('employees',[]);call.append('employees',{'employee':employee.name})
 call.set('dates',[]);call.append('dates',{'work_date':'2026-09-15','start_time':'18:00:00','end_time':'20:00:00','requested_hours':2})
 call.insert(ignore_permissions=True);call.flags.ignore_permissions=True;call.submit()
 names=frappe.get_all('Overtime Authorization',filters={'overtime_work_call':call.name},pluck='name');assert len(names)==1
 name=names[0];auth=frappe.get_doc('Overtime Authorization',name)
 assert auth.evidence_enrolled and not auth.auto_enrolled and auth.evidence_status=='Pending'
 checks.append('normal Work Call submit generated and enrolled verified mode without presumed enrollment')
 def punch(clock,kind,day='2026-09-15'):
  doc=frappe.get_doc({'doctype':'Employee Checkin','employee':employee.name,'time':day+' '+clock,'log_type':kind,'skip_auto_attendance':0})
  doc.insert(ignore_permissions=True);return doc
 first=punch('08:00:00','IN');punch('12:00:00','OUT');punch('13:00:00','IN')
 with patch.object(evidence,'now_datetime',return_value=get_datetime('2026-09-15 21:00:00')):
  assert evidence.process_authorization(name)=='Needs Review'
  assert frappe.db.get_value('Overtime Authorization',name,'verified_hours')==0
  last=punch('20:00:00','OUT')
  assert evidence.process_authorization(name)=='Verified'
  auth=frappe.get_doc('Overtime Authorization',name)
  assert auth.actual_start==get_datetime('2026-09-15 18:00:00') and auth.actual_end==get_datetime('2026-09-15 20:00:00')
  assert auth.verified_hours==2 and auth.presumed_hours==0 and auth.reconciliation_source=='Employee Checkin'
  assert frappe.db.get_value('Overtime Work Call',call.name,'verified_hours')==2
  snapshot=frappe.parse_json(auth.evidence_snapshot)
  assert not snapshot['weekly_evidence']['complete'] and snapshot['calculation']['unclassified_regular_hours']==2
  assert auth.regular_35_hours==auth.regular_100_hours==0
  checks.append('missing prior weekday preserves two verified hours with recargo pending, without assumed 44 hours')
  checks.append('late exit changes review to actual 18:00-20:00 / 2 hours and syncs Work Call')
  audit_count=frappe.db.count('Overtime Reconciliation Run',{'authorization':name})
  assert evidence.process_authorization(name)=='Verified'
  assert frappe.db.count('Overtime Reconciliation Run',{'authorization':name})==audit_count
  checks.append('idempotent evaluation has no duplicate immutable run')
  original_snapshot=auth.evidence_snapshot
  shift.db_set('last_sync_of_checkin','2026-09-17 08:00:00')
  punch('08:00:00','IN',day='2026-09-16')
  assert evidence.process_authorization(name)=='Verified'
  assert frappe.db.count('Overtime Reconciliation Run',{'authorization':name})==audit_count
  assert frappe.db.get_value('Overtime Authorization',name,'evidence_snapshot')==original_snapshot
  checks.append('advancing sync and next-day punches do not invalidate a completed snapshot')
  try:_validate_ready(auth)
  except frappe.ValidationError:pass
  else:raise AssertionError('Unapproved policy allowed settlement')
  checks.append('pending payroll policy blocks settlement independently of real-hour persistence')
  auth.evidence_settlement_ready=1
  try:evidence.validate_settlement(auth,for_update=True)
  except frappe.ValidationError:pass
  else:raise AssertionError('Readiness flag bypassed fresh evidence and policy validation')
  auth.evidence_settlement_ready=0
  checks.append('a readiness flag alone cannot bypass fresh evidence and policy verification')
  prior=punch('08:00:00','IN',day='2026-09-14');punch('18:00:00','OUT',day='2026-09-14')
  fresh=evidence.build_result(auth,for_update=True)
  assert fresh['weekly_evidence']['complete'] and fresh['calculation']['regular_35_hours']==2
  assert fresh['calculation']['segments'][0]['actual_weekly_hours_before']==19
  assert evidence.process_authorization(name)=='Needs Review'
  assert frappe.db.get_value('Overtime Authorization',name,'verified_hours')==2
  checks.append('late prior-weekday evidence recomputes actual 19-hour basis and flags the frozen dependent authorization')
  frozen=auth.evidence_snapshot
  last.time='2026-09-15 19:00:00';last.save(ignore_permissions=True)
  assert evidence.process_authorization(name)=='Needs Review'
  assert evidence.process_authorization(name)=='Needs Review'
  auth=frappe.get_doc('Overtime Authorization',name)
  assert auth.verified_hours==2 and auth.evidence_snapshot==frozen
  checks.append('post-verification source changes preserve frozen hours through repeated retries')
  auth.evidence_status='Verified'
  try:auth.save(ignore_permissions=True)
  except frappe.ValidationError:pass
  else:raise AssertionError('Generic save forged evidence status')
  checks.append('generic document save cannot forge service-owned evidence')
  frappe.db.set_value('Overtime Authorization',name,{'reconciliation_source':'Manual Verification','verified_hours':1})
  assert evidence.process_authorization(name)=='Manual Verification'
  assert frappe.db.get_value('Overtime Authorization',name,'verified_hours')==1
  checks.append('explicit HR verification is not overwritten by checkin retries')
 # A policy is approved only inside this rollback fixture, never in the live site state.
 policy=frappe.get_doc({'doctype':'Overtime Pay Policy','title':'DEV rollback policy','company':employee.company,
  'valid_from':'2026-09-01','valid_until':'2026-09-30','approval_reference':'Synthetic DEV acceptance only; must roll back',
  'weekly_threshold':68,'regular_percent':40,'extraordinary_percent':100,'night_percent':15,'weekly_rest_percent':100,
  'night_basis':'Clock overlap','premium_combination':'Additive on base hour'})
 policy.insert(ignore_permissions=True);policy.flags.ignore_permissions=True;policy.submit()
 assert policy.approved_by=='Administrator' and policy.approved_on
 overlap=frappe.copy_doc(policy);overlap.docstatus=0;overlap.insert(ignore_permissions=True);overlap.flags.ignore_permissions=True
 try:overlap.submit()
 except frappe.ValidationError:pass
 else:raise AssertionError('Overlapping policy approval succeeded')
 policy.regular_percent=45
 try:policy.save(ignore_permissions=True)
 except frappe.ValidationError:pass
 else:raise AssertionError('Submitted policy was editable')
 assert frappe.db.get_value('Overtime Pay Policy',policy.name,'regular_percent')==40
 checks.append('policy approval has identity, rejects overlapping validity and preserves approved rates')
 cash_employee=frappe.copy_doc(employee);cash_employee.name=prefix+'-CASH-EMP';cash_employee.docstatus=0;cash_employee.db_insert()
 original=frappe.get_all('Salary Structure Assignment',filters={'employee':base.employee,'docstatus':1},pluck='name',order_by='from_date desc',limit=1)
 assert original
 assignment=frappe.copy_doc(frappe.get_doc('Salary Structure Assignment',original[0]));assignment.name=prefix+'-SSA'
 assignment.employee=cash_employee.name;assignment.docstatus=1;assignment.from_date='2026-01-01';assignment.base=19064
 assignment.salary_per_hour=100;assignment.db_insert()
 def cash_call(day):
  source=frappe.copy_doc(frappe.get_doc('Overtime Work Call','CONV-HE-2026-00004-1'));source.name=None;source.docstatus=0
  source.company=employee.company;source.from_date=day;source.to_date=day;source.planned_settlement='Cash'
  source.automation_mode='Verified Checkins';source.evidence_auto_settle=1
  source.set('employees',[]);source.append('employees',{'employee':cash_employee.name})
  source.set('dates',[]);source.append('dates',{'work_date':day,'start_time':'18:00:00','end_time':'20:00:00','requested_hours':2})
  source.insert(ignore_permissions=True);source.flags.ignore_permissions=True;source.submit()
  for clock,kind in [('08:00:00','IN'),('12:00:00','OUT'),('13:00:00','IN'),('20:00:00','OUT')]:
   frappe.get_doc({'doctype':'Employee Checkin','employee':cash_employee.name,'time':day+' '+clock,'log_type':kind,'skip_auto_attendance':0}).insert(ignore_permissions=True)
  return source,frappe.db.get_value('Overtime Authorization',{'overtime_work_call':source.name},'name')
 from powerpro.controllers import overtime_settlement as settlement
 from powerpro.controllers.overtime_cash_settlement import _get_linked_additional_salaries
 frappe.db.set_single_value('DGII Payroll Settings','overtime_auto_payroll_date_policy','Work Date')
 first_call,first_auth=cash_call('2026-09-14')
 with patch.object(evidence,'now_datetime',return_value=get_datetime('2026-09-14 21:00:00')):
  assert evidence.process_authorization(first_auth)=='Frozen'
  paid_input=frappe.get_doc('Overtime Authorization',first_auth)
  refs=_get_linked_additional_salaries(paid_input,docstatus=1);assert len(refs)==1
  assert paid_input.verified_hours==2 and paid_input.presumed_hours==0 and paid_input.settlement_status=='Created'
  assert paid_input.settlement_amount==280
  breakdown=frappe.parse_json(paid_input.settlement_breakdown)
  assert breakdown['pay_policy']['name']==policy.name and breakdown['lines'][0]['premium_percent']==40
  assert evidence.process_authorization(first_auth)=='Frozen'
  assert refs==_get_linked_additional_salaries(paid_input,docstatus=1)
  checks.append('verified checkins automatically create one submitted Additional Salary at the approved 40 percent policy rate; retry creates none')
 second_call,second_auth=cash_call('2026-09-15')
 real_create=settlement.create_cash_settlement_for_source
 def fail_after_creation(*a,**kw):
  real_create(*a,**kw)
  raise RuntimeError('Synthetic failure after salary creation')
 before_salary_count=frappe.db.count('Additional Salary')
 with patch.object(evidence,'now_datetime',return_value=get_datetime('2026-09-15 21:00:00')):
  with patch.object(settlement,'create_cash_settlement_for_source',side_effect=fail_after_creation):
   assert evidence.process_authorization(second_auth)=='Verified'
  assert frappe.db.count('Additional Salary')==before_salary_count
  second=frappe.get_doc('Overtime Authorization',second_auth)
  assert second.verified_hours==2 and second.evidence_settlement_ready and 'settlement_error' in second.evidence_issues
  assert evidence.process_authorization(second_auth)=='Frozen'
  assert len(_get_linked_additional_salaries(second,docstatus=1))==1
  checks.append('failure after salary creation rolls back only settlement, preserves verified hours and succeeds once on retry')
 from powerpro.controllers import checkin_overtime_review as review
 with patch.object(evidence,'now_datetime',return_value=get_datetime('2026-09-16 21:00:00')):
  frappe.db.savepoint('test_prior_dependency')
  first_exit=frappe.get_doc('Employee Checkin',frappe.db.get_value('Employee Checkin',{'employee':cash_employee.name,'time':'2026-09-14 20:00:00'},'name'))
  first_exit.time='2026-09-14 19:00:00';first_exit.save(ignore_permissions=True)
  preview=review.preview_review(first_auth,'La salida corregida demuestra una hora menos.')
  assert preview['dependencies'][0]['name']==second_auth and preview['dependencies'][0]['blocks_reversal']
  try:review.apply_review(first_auth,preview['reason'],preview['token'])
  except frappe.ValidationError:pass
  else:raise AssertionError('Earlier correction bypassed settled weekly dependency')
  frappe.db.rollback(save_point='test_prior_dependency')
  frappe.db.value_cache.clear()
  exit_doc=frappe.get_doc('Employee Checkin',frappe.db.get_value('Employee Checkin',{'employee':cash_employee.name,'time':'2026-09-15 20:00:00'},'name'))
  exit_doc.time='2026-09-15 19:00:00';exit_doc.save(ignore_permissions=True)
  second.reload();old_snapshot=second.evidence_snapshot;old_refs=_get_linked_additional_salaries(second,docstatus=1)
  preview=review.preview_review(second_auth,'Salida temprana comprobada y revisada por Gestión Humana.')
  rules=preview['rules_summary']
  assert rules['policy']['name']==policy.name and rules['policy']['regular_percent']==40
  assert rules['policy']['night_basis']=='Clock overlap' and rules['hours']['verified_hours']==1
  assert rules['weekly_evidence_complete'] is True and 'rate_basis' not in rules
  checks.append('review GET describes the evaluated policy40 and one revised hour without exposing salary inputs')
  assert preview['before']['verified_hours']==2 and preview['after']['verified_hours']==1 and preview['settlement_ready'],evidence.build_result(second,use_saved_review=False)['weekly_evidence']['issues']
  assert preview['proposed_amount']==140
  frappe.db.savepoint('test_excluded_review')
  exit_doc.skip_auto_attendance=1;exit_doc.save(ignore_permissions=True)
  try:review.preview_review(second_auth,'No aceptar una salida excluida.')
  except frappe.ValidationError:pass
  else:raise AssertionError('HR review fabricated evidence from an excluded exit')
  frappe.db.rollback(save_point='test_excluded_review');exit_doc.reload()
  exit_doc.time='2026-09-15 19:30:00';exit_doc.save(ignore_permissions=True)
  try:review.apply_review(second_auth,preview['reason'],preview['token'])
  except frappe.ValidationError:pass
  else:raise AssertionError('Stale review token was accepted')
  exit_doc.time='2026-09-15 19:00:00';exit_doc.save(ignore_permissions=True)
  frappe.db.savepoint('test_payroll_guard')
  slip=frappe.new_doc('Salary Slip');slip.name=prefix+'-REVIEW-SLIP';slip.employee=cash_employee.name;slip.company=cash_employee.company;slip.docstatus=1;slip.db_insert()
  detail=frappe.new_doc('Salary Detail');detail.name=prefix+'-REVIEW-DETAIL';detail.docstatus=1;detail.parent=slip.name;detail.parenttype='Salary Slip';detail.parentfield='earnings';detail.additional_salary=old_refs[0];detail.db_insert()
  try:review.apply_review(second_auth,preview['reason'],preview['token'])
  except frappe.ValidationError:pass
  else:raise AssertionError('Review reversed payroll-included earnings')
  second.reload();assert second.evidence_snapshot==old_snapshot and _get_linked_additional_salaries(second,docstatus=1)==old_refs
  frappe.db.rollback(save_point='test_payroll_guard')
  with patch.object(settlement,'create_cash_settlement_for_source',side_effect=fail_after_creation):
   try:review.apply_review(second_auth,preview['reason'],preview['token'])
   except RuntimeError:pass
   else:raise AssertionError('Replacement failure was not propagated')
  second.reload();assert second.evidence_snapshot==old_snapshot and _get_linked_additional_salaries(second,docstatus=1)==old_refs
  outcome=review.apply_review(second_auth,preview['reason'],preview['token']);second.reload()
  assert outcome['status']=='Applied' and second.verified_hours==1 and second.settlement_amount==140
  assert all(frappe.db.get_value('Additional Salary',r,'docstatus')==2 for r in old_refs)
  replacement=_get_linked_additional_salaries(second,docstatus=1);assert len(replacement)==1
  again=review.apply_review(second_auth,preview['reason'],preview['token'])
  assert again['idempotent'] and again['audit']==outcome['audit']
  assert _get_linked_additional_salaries(second,docstatus=1)==replacement
  try:review.preview_review(second_auth,'Un motivo diferente no justifica duplicar lo ya aplicado.')
  except frappe.ValidationError:pass
  else:raise AssertionError('Unchanged reviewed evidence could be paid again')
  assert evidence.process_authorization(second_auth)=='Frozen'
  assert evidence.build_result(second,for_update=True)['settlement_ready']
  audit=frappe.parse_json(frappe.db.get_value('Overtime Reconciliation Run',outcome['audit'],'evidence'))
  assert audit['before']['snapshot']['verified_hours']==2 and audit['after']['snapshot']['verified_hours']==1
  checks.append('HR review accepts a measured shortfall; stale preview, submitted payroll and later settled week block it; failed replacement preserves original money and evidence; retry applies once with before/after audit')
 frappe.db.set_single_value('DGII Payroll Settings','enable_manual_overtime_verification',1)
 with patch.object(evidence,'now_datetime',return_value=get_datetime('2026-09-16 21:00:00')):
  exit_doc.reload();exit_doc.skip_auto_attendance=1;exit_doc.save(ignore_permissions=True)
  before_checkins=frappe.db.count('Employee Checkin')
  declaration={'full_session':True,'reference':'Parte del supervisor: jornada y pausas verificadas',
   'intervals':[{'start':'2026-09-15T08:00:00','end':'2026-09-15T12:00:00'},{'start':'2026-09-15T13:00:00','end':'2026-09-15T19:30:00'}]}
  manual=review.preview_review(second_auth,'Ponchada de salida inválida; referencia del supervisor revisada.',manual_declaration=declaration)
  assert manual['after']['verified_hours']==1.5 and manual['proposed_amount']==210,manual
  assert manual['checkin_comparison']['state']=='Needs Review'
  out=review.apply_review(second_auth,manual['reason'],manual['token'],manual_declaration=declaration)
  second.reload();assert second.reconciliation_source=='Manual Verification' and second.verified_hours==1.5 and second.settlement_amount==210
  assert frappe.db.count('Employee Checkin')==before_checkins
  assert evidence.process_authorization(second_auth)=='Frozen'
  third_call,third_auth=cash_call('2026-09-16')
  assert evidence.process_authorization(third_auth)=='Frozen'
  third=frappe.get_doc('Overtime Authorization',third_auth)
  saved=frappe.parse_json(third.evidence_snapshot)
  assert saved['weekly_evidence']['complete'] and saved['calculation']['segments'][0]['actual_weekly_hours_before']==30.5,saved['weekly_evidence']
  assert any(r['state']=='hr_certified_session' for r in saved['weekly_evidence']['coverage'])
  from powerpro.controllers.automatic_overtime import lock_payroll_inputs
  payroll_input=frappe._dict(employee=cash_employee.name,earnings=[frappe._dict(additional_salary=_get_linked_additional_salaries(second,docstatus=1)[0])])
  lock_payroll_inputs(payroll_input,'before_submit')
  frappe.db.savepoint('test_late_manual_evidence')
  exit_doc.reload();exit_doc.skip_auto_attendance=0;exit_doc.save(ignore_permissions=True)
  try:lock_payroll_inputs(payroll_input,'before_submit')
  except frappe.ValidationError:pass
  else:raise AssertionError('Payroll accepted newly changed evidence after manual certification')
  frappe.db.rollback(save_point='test_late_manual_evidence')
  checks.append('complete-session HR declaration resolves an invalid exit without changing Checkins, replaces cash at 1.5h/210, and supplies actual 10.5-hour day to later weekly bands')
 first_call.reload();first_call.flags.ignore_permissions=True;first_call.cancel()
 assert all(frappe.db.get_value('Additional Salary',ref,'docstatus')==2 for ref in refs)
 checks.append('cancelling the Work Call reverses its generated Additional Salary through document lifecycles')
 frappe.set_user('Guest')
 try:evidence.process_now(name)
 except frappe.PermissionError:pass
 else:raise AssertionError('Guest triggered a write')
 frappe.set_user('Administrator')
 print('DEV_CHECKIN_ACCEPTANCE',json.dumps(checks))
finally:
 frappe.db.rollback();frappe.db.commit=commit;frappe.sendmail=sendmail;frappe.enqueue=enqueue
 after={d:frappe.db.count(d) for d in counts}
 assert before==after,(before,after)
 assert frappe.db.get_singles_dict('DGII Payroll Settings')==original_settings
 print('ROLLBACK_COUNTS_UNCHANGED',json.dumps(after))
 frappe.db.rollback();frappe.destroy()
