"""DEV-only independent night premium; native document lifecycle, all rows rolled back."""
import json,uuid
from unittest.mock import patch
import frappe
from frappe.utils import get_datetime
frappe.init(site='igcaribe.fortabs.com');frappe.connect();frappe.set_user('Administrator')
assert frappe.local.site=='igcaribe.fortabs.com' and frappe.conf.developer_mode
from powerpro.controllers import ordinary_night as night
from powerpro.controllers.overtime_cash_settlement import _get_linked_additional_salaries
DT=night.DT
counts=['Shift Assignment','Employee','Shift Type','Employee Checkin','Overtime Authorization','Overtime Work Call','Overtime Reconciliation Run','Overtime Pay Policy',DT,'Additional Salary','Salary Slip','Salary Structure Assignment',
 'Working Time Incident','Working Time Review','Working Time Evidence Reference','Overtime Evidence Watch','Version','Error Log','User','Has Role','User Permission']
before={dt:frappe.db.count(dt) for dt in counts}
settings_before={dt:frappe.db.get_singles_dict(dt) for dt in ['DGII Payroll Settings','Payroll Settings']}
commit,enqueue,sendmail=frappe.db.commit,frappe.enqueue,frappe.sendmail

def forbidden(*a,**kw):raise AssertionError('Commit or outbound effect forbidden')
frappe.db.commit=forbidden;frappe.enqueue=forbidden;frappe.sendmail=forbidden
prefix='NIGHT-DEV-'+uuid.uuid4().hex[:8]
try:
 frappe.db.set_single_value('DGII Payroll Settings',{'enable_checkin_overtime_reconciliation':1,'checkin_overtime_effective_from':'2026-09-01'})
 frappe.db.set_single_value('Payroll Settings','email_salary_slip_to_employee',0)
 base=frappe.get_doc('Overtime Authorization','AUT-HE-2026-00018')
 shift=frappe.copy_doc(frappe.get_doc('Shift Type','Diurna Extendida'));shift.name=prefix+'-SHIFT';shift.docstatus=0
 shift.start_time='18:00:00';shift.end_time='02:00:00';shift.enable_auto_attendance=0
 shift.begin_check_in_before_shift_start_time=0;shift.allow_check_out_after_shift_end_time=0
 shift.determine_check_in_and_check_out='Alternating entries as IN and OUT during the same shift';shift.working_hours_calculation_based_on='Every Valid Check-in and Check-out'
 shift.last_sync_of_checkin='2026-09-30 23:00:00';shift.db_insert()
 employee=frappe.copy_doc(frappe.get_doc('Employee',base.employee));employee.name=prefix+'-EMP';employee.docstatus=0
 employee.employee_name='DEV Night';employee.user_id=None;employee.company_email=None;employee.personal_email=None
 employee.default_shift=shift.name;employee.status='Active';employee.db_insert()
 assignment_name=frappe.get_all('Salary Structure Assignment',filters={'employee':base.employee,'docstatus':1},pluck='name',order_by='from_date desc',limit=1)[0]
 assignment=frappe.copy_doc(frappe.get_doc('Salary Structure Assignment',assignment_name));assignment.name=prefix+'-SSA';assignment.employee=employee.name
 assignment.docstatus=1;assignment.from_date='2026-01-01';assignment.base=19064;assignment.salary_per_hour=100;assignment.db_insert()
 policy=frappe.get_doc({'doctype':'Overtime Pay Policy','title':'DEV ordinary night','company':employee.company,
  'valid_from':'2026-09-01','valid_until':'2026-09-30','approval_reference':'Synthetic rollback test, not a real approval',
  'weekly_threshold':68,'regular_percent':35,'extraordinary_percent':100,'night_percent':15,'weekly_rest_percent':100,
  'night_basis':'Clock overlap','premium_combination':'Additive on base hour','enable_compensatory':0})
 policy.insert(ignore_permissions=True);policy.flags.ignore_permissions=True;policy.submit()
 def punch(stamp,kind):
  doc=frappe.get_doc({'doctype':'Employee Checkin','employee':employee.name,'time':stamp,'log_type':kind});doc.insert(ignore_permissions=True);return doc
 first=punch('2026-09-14 18:00:00','IN');last=punch('2026-09-15 02:00:00','OUT')
 def draft():
  doc=frappe.get_doc({'doctype':DT,'employee':employee.name,'work_date':'2026-09-14','settlement_payroll_date':'2026-09-15','review_reference':'DEV synthetic reference'})
  doc.insert(ignore_permissions=True);doc.flags.ignore_permissions=True;return doc
 with patch.object(night,'now_datetime',return_value=get_datetime('2026-09-16 10:00:00')):
  doc=draft();assert doc.evidence_status=='Verified' and doc.night_hours==5 and doc.settlement_amount==75
  doc.submit();doc.reload();assert doc.settlement_status=='Created'
  refs=_get_linked_additional_salaries(doc,docstatus=1);assert len(refs)==1
  assert frappe.db.count('Overtime Authorization')==before['Overtime Authorization']
  frappe.db.savepoint('duplicate_night_draft')
  duplicate=draft()
  try:duplicate.submit()
  except (frappe.ValidationError,frappe.UniqueValidationError):pass
  else:raise AssertionError('Duplicate ordinary night settlement accepted')
  frappe.db.rollback(save_point='duplicate_night_draft')
  salary=frappe.get_doc('Additional Salary',refs[0]);salary.flags.ignore_permissions=True
  try:salary.cancel()
  except frappe.ValidationError:pass
  else:raise AssertionError('Direct salary cancellation bypassed source')
  from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
  slip=make_salary_slip(assignment.salary_structure,employee=employee.name,posting_date='2026-09-15',ignore_permissions=True)
  slip.insert(ignore_permissions=True);slip.flags.ignore_permissions=True
  last.time='2026-09-15 01:00:00';last.save(ignore_permissions=True)
  assert night.get_status(doc.name)['state']=='Needs Review'
  try:slip.submit()
  except frappe.ValidationError:pass
  else:raise AssertionError('Payroll accepted stale night evidence')
  last.time='2026-09-15 02:00:00';last.save(ignore_permissions=True)
  slip.reload();slip.flags.ignore_permissions=True;slip.submit();doc.reload()
  assert doc.settlement_status=='Payroll Submitted' and doc.settlement_salary_slip==slip.name
  try:doc.cancel()
  except frappe.ValidationError:pass
  else:raise AssertionError('Source cancellation bypassed submitted payroll')
  slip.cancel();doc.reload();doc.flags.ignore_permissions=True;doc.cancel();doc.reload()
  assert doc.docstatus==2 and not doc.active_claim and frappe.db.get_value('Additional Salary',refs[0],'docstatus')==2
  # Cancelled night earnings retain physical evidence independently of current
  # salary/policy. Historical corrections never revive the cancelled source.
  from powerpro.controllers import ordinary_night_history as history,working_time_controls as controls
  from powerpro.controllers import working_time_incidents as cases,working_time_reviews as reviews,overtime_evidence_monitor as monitor
  from powerpro.controllers import overtime_cash_settlement as cash
  frappe.db.set_single_value('DGII Payroll Settings',{'enable_overtime_evidence_monitor':1,
   'enable_working_time_incident_monitor':1,'enable_manual_overtime_verification':1})
  def fails(fn,exc=frappe.ValidationError):
   try:fn()
   except exc:return
   raise AssertionError('Expected refusal')
  frozen_source=doc.as_dict();money=frappe.db.count('Additional Salary');marks=frappe.db.count('Employee Checkin')
  with (patch.object(night,'get_effective_policy',side_effect=AssertionError('History read financial policy')),
        patch.object(cash,'_get_hourly_rate',side_effect=AssertionError('History read salary rate'))):
   assert history.compare(doc)['matches']
  assert night.get_status(doc.name)['state']=='Verified' and monitor.check_source(DT,doc.name)['status']=='Current'
  # Explicit observations retain physical overruns without reviving earnings.
  frappe.db.savepoint('night_observation')
  observed={'start':'2026-09-14 18:00:00','end':'2026-09-15 06:00:00'}
  last.time='2026-09-15 06:00:00';last.log_type='IN';last.save(ignore_permissions=True)
  fails(lambda:history.preview_review(doc.name,'Missing original exit'))
  with patch.object(night,'now_datetime',return_value=get_datetime('2026-09-15 05:00:00')):
   fails(lambda:history.preview_review(doc.name,'Future physical exit',observation_window=observed))
  with (patch.object(night,'get_effective_policy',side_effect=AssertionError('Historical expansion read pay policy')),
        patch.object(cash,'_get_hourly_rate',side_effect=AssertionError('Historical expansion read rate'))):
   p=history.preview_review(doc.name,'DEV expanded night',observation_window=json.dumps(observed))
   assert p['worked_hours_before']==8 and p['worked_hours_after']==12 and not p['settlement_ready']
   assert p['unapproved_intervals']==[{'start':'2026-09-15T02:00:00','end':'2026-09-15T06:00:00'}]
   assert p['source_checkins'][-1]['log_type']=='IN'
   last.time='2026-09-15 05:30:00';last.save(ignore_permissions=True)
   fails(lambda:history.apply_review(doc.name,'DEV expanded night',p['token'],observation_window=observed))
   last.time='2026-09-15 06:00:00';last.save(ignore_permissions=True)
   p=history.preview_review(doc.name,'DEV expanded night',observation_window=observed)
   accepted=history.apply_review(doc.name,'DEV expanded night',p['token'],observation_window=p['observation_window'])
   assert history.apply_review(doc.name,'DEV expanded night',p['token'],observation_window=observed)['idempotent']
   assert history.compare(doc)['matches']
  assert get_datetime(history.get_status(doc.name)['observation_window']['end'])==get_datetime(observed['end'])
  assert monitor.check_source(DT,doc.name)['status']=='Current'
  diagnostic=controls.preview(DT,doc.name);assert diagnostic['historical_review']['accepted']
  assert get_datetime(diagnostic['supporting_evidence']['weekly']['cutoff'])==get_datetime(observed['end'])
  fails(lambda:history.preview_review(doc.name,'Cannot shorten night',observation_window={'start':observed['start'],'end':'2026-09-15 05:00:00'}))
  last.skip_auto_attendance=1;last.save(ignore_permissions=True)
  fails(lambda:history.preview_review(doc.name,'Excluded night exit'))
  declaration={'full_session':True,'reference':'DEV supervisor expanded full night','intervals':[
   {'start':'2026-09-14 18:00:00','end':'2026-09-14 22:00:00'},
   {'start':'2026-09-14 23:00:00','end':'2026-09-15 06:00:00'}]}
  p=history.preview_review(doc.name,'DEV expanded manual night',declaration)
  assert p['worked_hours_after']==11
  history.apply_review(doc.name,'DEV expanded manual night',p['token'],declaration)
  assert history.compare(doc)['matches']
  doc.reload();assert doc.as_dict()==frozen_source and frappe.db.count('Additional Salary')==money and frappe.db.count('Employee Checkin')==marks
  frappe.db.rollback(save_point='night_observation');last.reload();doc.reload()
  assert history.compare(doc)['matches']
  # Previous date has a DIFFERENT actual Shift Assignment ending this morning.
  # A broad explicit window must not silently adopt that shift's 04:00 mark.
  frappe.db.savepoint('night_prior_shift')
  prior=frappe.copy_doc(shift);prior.name=prefix+'-PRIOR';prior.docstatus=0;prior.start_time='22:00:00';prior.end_time='06:00:00';prior.db_insert()
  frappe.get_doc({'doctype':'Shift Assignment','employee':employee.name,'shift_type':prior.name,
   'start_date':'2026-09-13','end_date':'2026-09-13','status':'Active','docstatus':1}).db_insert()
  first.time='2026-09-14 04:00:00';first.save(ignore_permissions=True)
  backward={'start':'2026-09-14 03:00:00','end':'2026-09-15 02:00:00'}
  current=history.evaluate(doc,frappe.parse_json(doc.evidence_snapshot),observation_window=backward)
  assert any(w.get('relation')=='previous' and w['shift']==prior.name for w in current['input']['next_windows'])
  assert any(i['code']=='adjacent_shift_overlap' for i in current['issues'])
  fails(lambda:history.preview_review(doc.name,'Ambiguous earlier shift',observation_window=backward))
  declaration={'full_session':True,'reference':'DEV supervisor assigns exact complete session','intervals':[
   {'start':'2026-09-14 18:00:00','end':'2026-09-15 02:00:00'}]}
  p=history.preview_review(doc.name,'DEV resolve earlier shift',declaration,observation_window=backward)
  assert p['worked_hours_after']==8
  history.apply_review(doc.name,'DEV resolve earlier shift',p['token'],declaration,observation_window=backward)
  assert history.compare(doc)['matches']
  assert frappe.db.count('Employee Checkin')==marks and frappe.db.count('Additional Salary')==money
  frappe.db.rollback(save_point='night_prior_shift');first.reload();last.reload();doc.reload()
  assert history.compare(doc)['matches']
  print('NIGHT_OBSERVATION: explicit12h/raw11h/manual, no new pay, original IN retained, actual cutoff, stale/idempotent/no-shrink, previous different Shift Assignment ambiguity and explicit documented resolution passed')
  diagnostic=controls.preview(DT,doc.name);assert diagnostic['historical_review']['accepted']
  rows=cases.record(DT,doc.name,{},'Administrator',diagnostic['input_hash'])
  pause=frappe.get_doc(cases.DT,next(r['name'] for r in rows if frappe.db.get_value(cases.DT,r['name'],'control_code')=='work_break'))
  cases.resolve(pause.name,pause.evidence_hash,'Documented Exception','DEV historical eight hours without pause','DEV source')
  last.time='2026-09-15 01:00:00';last.save(ignore_permissions=True)
  assert monitor.check_source(DT,doc.name)['status']=='Needs Review' and night.get_status(doc.name)['state']=='Needs Review'
  cases.recheck(pause.name);pause.reload();assert pause.status=='Open' and pause.evaluation_status=='Historical review required'
  fails(lambda:cases.resolve(pause.name,pause.evidence_hash,'Documented Exception','Cancelled payment','DEV'))
  p=history.preview_review(doc.name,'DEV corrected physical exit');assert p['worked_hours_before']==8 and p['worked_hours_after']==7
  last.time='2026-09-15 00:00:00';last.save(ignore_permissions=True)
  fails(lambda:history.apply_review(doc.name,'DEV corrected physical exit',p['token']))
  last.time='2026-09-15 01:00:00';last.save(ignore_permissions=True)
  p=history.preview_review(doc.name,'DEV corrected physical exit')
  result=history.apply_review(doc.name,'DEV corrected physical exit',p['token']);assert result['history_sequence']==1
  assert history.apply_review(doc.name,'DEV corrected physical exit',p['token'])['idempotent']
  assert reviews.process_review(pause.working_time_review)['status']=='Checked'
  pause.reload();assert pause.evaluation_status=='Review' and pause.resolution_reference=='DEV source'
  assert any(r.document_type=='Overtime Reconciliation Run' and r.document_name==result['audit'] for r in pause.evidence_references)
  assert monitor.check_source(DT,doc.name)['status']=='Current'
  last.skip_auto_attendance=1;last.save(ignore_permissions=True)
  fails(lambda:history.preview_review(doc.name,'DEV missing exit'))
  declaration={'full_session':True,'reference':'DEV supervisor full session with pause','intervals':[
   {'start':'2026-09-14 18:00:00','end':'2026-09-14 22:00:00'},
   {'start':'2026-09-14 23:00:00','end':'2026-09-15 01:00:00'}]}
  p=history.preview_review(doc.name,'DEV documented historical pause',declaration)
  result=history.apply_review(doc.name,'DEV documented historical pause',p['token'],declaration);assert result['history_sequence']==2
  assert history.compare(doc)['matches']
  cases.recheck(pause.name);pause.reload();assert pause.evaluation_status==cases.CLEAR
  cases.resolve(pause.name,pause.evidence_hash,'Resolved','DEV complete declaration, four hours then two','DEV historical pause')
  assert not cases.recheck(pause.name)['changed']
  # Native role and evidence-reference permissions guard the historical API.
  user_name=prefix.lower()+'@example.invalid'
  frappe.get_doc({'doctype':'User','name':user_name,'email':user_name,'first_name':'DEV Night History Reviewer','enabled':1,
   'user_type':'System User','send_welcome_email':0}).db_insert()
  frappe.get_doc({'doctype':'Has Role','parent':user_name,'parenttype':'User','parentfield':'roles','role':'HR Manager'}).db_insert()
  frappe.get_doc({'doctype':'User Permission','user':user_name,'allow':'Employee','for_value':employee.name,'apply_to_all_doctypes':1}).db_insert()
  configured=frappe.db.get_single_value('DGII Payroll Settings','overtime_manual_verification_roles') or ''
  frappe.db.set_single_value('DGII Payroll Settings','overtime_manual_verification_roles',configured+'\nHR Manager')
  frappe.clear_cache(user=user_name);frappe.set_user(user_name)
  try:
   assert history.get_status(doc.name)['can_review']
   assert history.get_status(doc.name)['state']=='Verified'
   assert frappe.get_list(cases.DT,filters={'name':pause.name},pluck='name')
  finally:frappe.set_user('Administrator')
  frappe.get_doc({'doctype':'User Permission','user':user_name,'allow':'Employee Checkin','for_value':first.name,'apply_to_all_doctypes':1}).db_insert()
  frappe.clear_cache(user=user_name);frappe.set_user(user_name)
  try:
   fails(lambda:history.get_status(doc.name),frappe.PermissionError)
   fails(lambda:history.preview_review(doc.name,'Hidden mark',declaration),frappe.PermissionError)
   fails(lambda:cases.recheck(pause.name),frappe.PermissionError)
   assert not frappe.get_list(cases.DT,filters={'name':pause.name},pluck='name')
  finally:frappe.set_user('Administrator')
  last.skip_auto_attendance=0;last.time='2026-09-15 02:00:00';last.save(ignore_permissions=True)
  assert reviews.process_review(pause.working_time_review)['status']=='Checked'
  pause.reload();assert pause.status=='Open' and pause.evaluation_status=='Historical review required'
  assert pause.resolution_reference=='DEV historical pause'
  doc.reload();assert doc.as_dict()==frozen_source and frappe.db.count('Additional Salary')==money and frappe.db.count('Employee Checkin')==marks
  print('NIGHT_HISTORY: financial-independent physical evidence, audited correction, stale/idempotent guards, manual complete session, incident resolution/reopening and unchanged source/earnings passed')
  corrected=draft();corrected.submit()
  assert len(_get_linked_additional_salaries(corrected,docstatus=1))==1
  corrected.flags.ignore_permissions=True;corrected.cancel()
  # A separate ordinary+OT journey: the same evidence has one premium in each
  # category. Cancelled fixtures above have no remaining active claim.
  next_shift=frappe.copy_doc(shift);next_shift.name=prefix+'-SECOND-SHIFT';next_shift.docstatus=0;next_shift.start_time='16:00:00';next_shift.end_time='22:00:00';next_shift.db_insert()
  employee.db_set('default_shift',next_shift.name)
  frappe.db.value_cache.clear()
  first.reload();first.shift=None;first.save(ignore_permissions=True)
  last.reload();last.time='2026-09-14 23:00:00';last.shift=None;last.save(ignore_permissions=True)
  from powerpro.controllers import checkin_overtime as evidence
  call=frappe.copy_doc(frappe.get_doc('Overtime Work Call','CONV-HE-2026-00004-1'));call.name=None;call.docstatus=0
  call.company=employee.company;call.from_date='2026-09-14';call.to_date='2026-09-14';call.planned_settlement='Cash'
  call.automation_mode='Verified Checkins';call.evidence_auto_settle=1
  call.set('employees',[]);call.append('employees',{'employee':employee.name})
  call.set('dates',[]);call.append('dates',{'work_date':'2026-09-14','start_time':'22:00:00','end_time':'23:00:00','requested_hours':1})
  call.insert(ignore_permissions=True);call.flags.ignore_permissions=True;call.submit()
  auth_name=frappe.db.get_value('Overtime Authorization',{'overtime_work_call':call.name},'name')
  with patch.object(evidence,'now_datetime',return_value=get_datetime('2026-09-16 10:00:00')):
   result=evidence.process_authorization(auth_name)
   auth=frappe.get_doc('Overtime Authorization',auth_name)
   assert result=='Verified' and not auth.evidence_settlement_ready,(result,auth.evidence_issues)
   ordinary=draft();assert ordinary.night_hours==1 and ordinary.settlement_amount==15
   ordinary.submit()
   result=evidence.process_authorization(auth_name);auth.reload()
   assert result=='Frozen',(result,auth.evidence_issues)
   assert auth.night_hours==1 and auth.settlement_amount==150,(auth.night_hours,auth.settlement_amount)
   snapshot=frappe.parse_json(auth.evidence_snapshot)
   assert snapshot['ordinary_night_settlement']['name']==ordinary.name
   try:ordinary.cancel()
   except frappe.ValidationError:pass
   else:raise AssertionError('Ordinary coverage could be cancelled before linked OT')
   call.reload();call.flags.ignore_permissions=True;call.cancel()
   # A broader historical observation must include the still-paid ordinary
   # night dependency before accepting new work beyond the old OT window.
   from powerpro.controllers import overtime_history as auth_history
   last.reload();last.time='2026-09-15 02:00:00';last.save(ignore_permissions=True)
   observed={'start':'2026-09-14 16:00:00','end':'2026-09-15 02:00:00'}
   expanded=auth_history.preview_review(auth_name,'DEV dependent night window',observation_window=observed)
   assert any(r['name']==ordinary.name and r['doctype']==DT and r['blocks_reversal'] for r in expanded['dependencies'])
   fails(lambda:auth_history.apply_review(auth_name,'DEV dependent night window',expanded['token'],observation_window=observed))
   ordinary.reload();ordinary.flags.ignore_permissions=True;ordinary.cancel()
   expanded=auth_history.preview_review(auth_name,'DEV dependent night window',observation_window=observed)
   auth_history.apply_review(auth_name,'DEV dependent night window',expanded['token'],observation_window=observed)
   last.reload();last.time='2026-09-14 23:00:00';last.save(ignore_permissions=True)
   assert history.compare(ordinary)['matches'],'Cancelled authorization must preserve the documented extended session'
   assert controls.preview(DT,ordinary.name)['historical_review']['accepted']
  # Explicit policy opt-in lets an automatically enrolled authorization create
  # ordinary night and OT atomically. No historical/manual draft is taken over.
  frappe.db.savepoint('automatic_night_case')
  assert not frappe.db.count(DT,{'employee':employee.name,'docstatus':0})
  policy.flags.ignore_permissions=True;policy.cancel()
  auto_policy=frappe.copy_doc(policy);auto_policy.name=None;auto_policy.docstatus=0;auto_policy.auto_ordinary_night=1
  auto_policy.insert(ignore_permissions=True);auto_policy.flags.ignore_permissions=True;auto_policy.submit()
  def automatic_call():
   candidate=frappe.copy_doc(call);candidate.name=None;candidate.docstatus=0
   from powerpro.controllers.automatic_overtime import CALL_FIELDS
   for field in CALL_FIELDS+('evidence_reconciliation_enabled',):candidate.set(field,None)
   candidate.insert(ignore_permissions=True);candidate.flags.ignore_permissions=True;candidate.submit()
   return candidate,frappe.db.get_value('Overtime Authorization',{'overtime_work_call':candidate.name},'name')
  with patch.object(evidence,'now_datetime',return_value=get_datetime('2026-09-16 10:00:00')):
   from powerpro.controllers import overtime_settlement
   auto_call,auto_name=automatic_call()
   salaries_before=frappe.db.count('Additional Salary')
   frappe.db.savepoint('human_night_draft')
   human_draft=draft();human_snapshot=human_draft.evidence_snapshot
   assert evidence.process_authorization(auto_name)=='Verified'
   human_draft.reload();assert human_draft.docstatus==0 and human_draft.evidence_snapshot==human_snapshot
   assert frappe.db.count('Additional Salary')==salaries_before
   assert 'Ya existe una liquidación nocturna' in frappe.db.get_value('Overtime Authorization',auto_name,'evidence_issues')
   frappe.db.rollback(save_point='human_night_draft')
   settle=overtime_settlement._settle_authorization
   def fail_after_both(*args,**kwargs):
    settle(*args,**kwargs)
    raise ValueError('Injected failure after both financial obligations')
   with patch.object(overtime_settlement,'_settle_authorization',side_effect=fail_after_both):
    assert evidence.process_authorization(auto_name)=='Verified'
   failed=frappe.get_doc('Overtime Authorization',auto_name)
   assert failed.verified_hours==1 and not failed.evidence_settlement_ready
   assert 'Injected failure' in failed.evidence_issues
   assert frappe.db.count('Additional Salary')==salaries_before
   assert frappe.db.count(DT,{'employee':employee.name,'docstatus':1})==0
   assert evidence.process_authorization(auto_name)=='Frozen'
   automatic=frappe.get_doc('Overtime Authorization',auto_name)
   automatic_night=frappe.get_doc(DT,frappe.parse_json(automatic.evidence_snapshot)['ordinary_night_settlement']['name'])
   assert automatic_night.settlement_amount==15 and automatic.settlement_amount==150
   assert automatic.name in automatic_night.review_reference
   assert frappe.db.count('Additional Salary')==salaries_before+3
   assert evidence.process_authorization(auto_name)=='Frozen'
   assert frappe.db.count('Additional Salary')==salaries_before+3
   auto_call.reload();auto_call.flags.ignore_permissions=True;auto_call.cancel()
   automatic_night.reload();automatic_night.flags.ignore_permissions=True;automatic_night.cancel()
   # The opt-in can also resume a complete-session HR declaration, preserving it.
   frappe.db.set_single_value('DGII Payroll Settings','enable_manual_overtime_verification',1)
   last.reload();last.skip_auto_attendance=1;last.save(ignore_permissions=True)
   declared_call,declared_name=automatic_call()
   from powerpro.controllers import checkin_overtime_review as review
   declaration={'full_session':True,'reference':'DEV automatic night with certified session',
       'intervals':[{'start':'2026-09-14 18:00:00','end':'2026-09-14 23:00:00'}]}
   preview=review.preview_review(declared_name,'DEV certified complete session',manual_declaration=declaration)
   review.apply_review(declared_name,'DEV certified complete session',preview['token'],manual_declaration=declaration)
   assert evidence.process_authorization(declared_name)=='Frozen'
   declared=frappe.get_doc('Overtime Authorization',declared_name)
   declared_night=frappe.get_doc(DT,frappe.parse_json(declared.evidence_snapshot)['ordinary_night_settlement']['name'])
   assert declared.reconciliation_source=='Manual Verification'
   assert frappe.parse_json(declared_night.evidence_snapshot)['input']['certified_session']['authorization']==declared_name
   assert declared_night.settlement_amount==15 and declared.settlement_amount==150
  frappe.db.rollback(save_point='automatic_night_case');policy.reload();last.reload()
  print('NIGHT_AUTOMATIC_ACCEPTANCE: explicit approved policy plus enrolled auto authorization creates both obligations, failure reverses both and preserves hours, retry once, HR declaration retained')
  # Missing/invalid exit: certify once through the real HR review API, then
  # reuse it for ordinary night and resume the pending OT without changing source.
  frappe.db.set_single_value('DGII Payroll Settings','enable_manual_overtime_verification',1)
  last.reload();last.skip_auto_attendance=1;last.save(ignore_permissions=True)
  manual_call=frappe.copy_doc(call);manual_call.name=None;manual_call.docstatus=0
  from powerpro.controllers.automatic_overtime import CALL_FIELDS
  for field in CALL_FIELDS+('evidence_reconciliation_enabled',):manual_call.set(field,None)
  manual_call.insert(ignore_permissions=True);manual_call.flags.ignore_permissions=True;manual_call.submit()
  manual_name=frappe.db.get_value('Overtime Authorization',{'overtime_work_call':manual_call.name},'name')
  from powerpro.controllers import checkin_overtime_review as review
  with patch.object(evidence,'now_datetime',return_value=get_datetime('2026-09-16 10:00:00')):
   assert evidence.process_authorization(manual_name)=='Needs Review'
   declaration={'full_session':True,'reference':'DEV supervisor signed complete session',
       'intervals':[{'start':'2026-09-14 18:00:00','end':'2026-09-14 23:00:00'}]}
   punch_count=frappe.db.count('Employee Checkin')
   preview=review.preview_review(manual_name,'DEV missing exit confirmed by supervisor',manual_declaration=declaration)
   review.apply_review(manual_name,'DEV missing exit confirmed by supervisor',preview['token'],manual_declaration=declaration)
   manual=frappe.get_doc('Overtime Authorization',manual_name)
   assert manual.reconciliation_source=='Manual Verification' and not manual.evidence_settlement_ready
   frozen=frappe.parse_json(manual.evidence_snapshot);identity=(manual.reconciled_by,manual.reconciled_on)
   manual_night=draft()
   night_snapshot=frappe.parse_json(manual_night.evidence_snapshot)
   assert night_snapshot['input']['certified_session']['authorization']==manual.name
   assert manual_night.night_hours==1 and manual_night.settlement_amount==15
   # A changed raw punch cannot silently reuse HR's declaration.
   frappe.db.savepoint('night_manual_stale')
   last.skip_auto_attendance=0;last.save(ignore_permissions=True)
   try:manual_night.submit()
   except frappe.ValidationError:pass
   else:raise AssertionError('Night settlement accepted changed manual evidence')
   frappe.db.rollback(save_point='night_manual_stale');manual_night.reload();manual_night.flags.ignore_permissions=True
   manual_night.submit()
   assert evidence.process_authorization(manual.name)=='Frozen'
   manual.reload();assert manual.reconciliation_source=='Manual Verification' and manual.settlement_amount==150
   current=frappe.parse_json(manual.evidence_snapshot)
   assert current['review']==frozen['review'] and current['snapshot']==frozen['snapshot']
   assert identity==(manual.reconciled_by,manual.reconciled_on)
   assert current['ordinary_night_settlement']['name']==manual_night.name
   salary_count=frappe.db.count('Additional Salary')
   assert evidence.process_authorization(manual.name)=='Frozen'
   assert frappe.db.count('Additional Salary')==salary_count and frappe.db.count('Employee Checkin')==punch_count
   # Payroll must validate both documents through their actual native lifecycle.
   manual_slip=make_salary_slip(assignment.salary_structure,employee=employee.name,posting_date='2026-09-15',ignore_permissions=True)
   manual_slip.insert(ignore_permissions=True);manual_slip.flags.ignore_permissions=True;manual_slip.submit()
   manual.reload();manual_night.reload()
   assert manual.settlement_status==manual_night.settlement_status=='Payroll Submitted'
   manual_slip.cancel();manual_call.reload();manual_call.flags.ignore_permissions=True;manual_call.cancel()
   manual_night.reload();manual_night.flags.ignore_permissions=True;manual_night.cancel()
   assert history.compare(manual_night)['matches'],'Cancelled manual authorization must retain the approved declaration'
   assert controls.preview(DT,manual_night.name)['historical_review']['accepted']
  print('NIGHT_MANUAL_ACCEPTANCE: one HR declaration reused, 15 ordinary plus 150 OT, unchanged source/actor/punches, stale source rejected, idempotent resume and native payroll/cancel')
 print('NIGHT_ACCEPTANCE: no OT document, verified 5 ordinary night hours / 75 premium, duplicate and direct-cancel guards, stale evidence blocks native payroll, native submit/cancel, corrected replacement')
 print('NIGHT_OT_ACCEPTANCE: ordinary premium 15 plus OT 135 and extra night premium 15, distinct sources and protected cancellation order')
finally:
 frappe.set_user('Administrator');frappe.db.rollback();frappe.db.commit=commit;frappe.enqueue=enqueue;frappe.sendmail=sendmail
 after={dt:frappe.db.count(dt) for dt in counts};assert before==after,(before,after)
 assert settings_before=={dt:frappe.db.get_singles_dict(dt) for dt in settings_before}
 print('NIGHT_ROLLBACK_UNCHANGED',json.dumps(after));frappe.db.rollback();frappe.destroy()
