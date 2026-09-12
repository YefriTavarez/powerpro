"""DEV-only native credit/leave/election lifecycle acceptance. All data rolled back."""
import json,uuid
from datetime import timedelta
from unittest.mock import patch
import frappe
from frappe.utils import getdate,get_datetime
SITE='igcaribe.fortabs.com'
frappe.init(site=SITE);frappe.connect();frappe.set_user('Administrator')
assert frappe.local.site==SITE and frappe.conf.developer_mode
from powerpro.controllers import checkin_overtime as evidence,overtime_rest as rest,retroactive_evidence as retro
from powerpro.controllers.overtime import get_schedule_context
from powerpro.controllers.overtime_cash_settlement import _get_linked_additional_salaries
prefix='RETRO-REST-DEV-'+uuid.uuid4().hex[:10]
types=['Employee','Shift Type','Employee Checkin','Attendance','Overtime Authorization','Overtime Work Call','Retroactive Overtime Adjustment',
       'Overtime Pay Policy','Overtime Settlement Election','Overtime Reconciliation Run','Overtime Compensatory Credit',
       'Leave Period','Leave Allocation','Leave Application','Leave Ledger Entry','Additional Salary','Salary Slip','Salary Structure Assignment']
before={d:frappe.db.count(d) for d in types}
settings_before={d:frappe.db.get_singles_dict(d) for d in ['DGII Payroll Settings','HR Settings','Payroll Settings']}
commit,enqueue,sendmail=frappe.db.commit,frappe.enqueue,frappe.sendmail
def forbidden(*a,**kw):raise AssertionError('Commit or outbound effect in rollback fixture')
frappe.db.commit=forbidden;frappe.enqueue=forbidden;frappe.sendmail=forbidden
checks=[]
try:
 frappe.db.set_single_value('DGII Payroll Settings',{'enable_checkin_overtime_reconciliation':1,'checkin_overtime_effective_from':'2026-08-01',
  'enable_overtime_compensatory_settlement':1,'overtime_auto_payroll_date_policy':'Work Date',
  'enable_retroactive_overtime_adjustment':1,'retroactive_overtime_from_date':'2026-08-01','retroactive_overtime_to_date':'2026-09-23','retroactive_overtime_submission_deadline':'2026-09-23'})
 frappe.db.set_single_value('HR Settings','send_leave_notification',0)
 frappe.db.set_single_value('Payroll Settings','email_salary_slip_to_employee',0)
 base=frappe.get_doc('Overtime Authorization','AUT-HE-2026-00018')
 employee=frappe.copy_doc(frappe.get_doc('Employee',base.employee));employee.name=prefix+'-EMP';employee.docstatus=0
 employee.overtime_approver='Administrator';employee.status='Active';employee.employee_name='DEV Rest';employee.user_id=None;employee.company_email=None;employee.personal_email=None
 shift=frappe.copy_doc(frappe.get_doc('Shift Type','Diurna Extendida'));shift.name=prefix+'-SHIFT';shift.docstatus=0;shift.enable_auto_attendance=0
 shift.determine_check_in_and_check_out='Alternating entries as IN and OUT during the same shift';shift.working_hours_calculation_based_on='Every Valid Check-in and Check-out'
 shift.last_sync_of_checkin='2026-09-23 23:00:00';shift.db_insert();employee.default_shift=shift.name;employee.db_insert()
 original=frappe.get_all('Salary Structure Assignment',filters={'employee':base.employee,'docstatus':1},pluck='name',order_by='from_date desc',limit=1)
 assignment=frappe.copy_doc(frappe.get_doc('Salary Structure Assignment',original[0]));assignment.name=prefix+'-SSA';assignment.employee=employee.name
 assignment.docstatus=1;assignment.from_date='2026-01-01';assignment.base=19064;assignment.salary_per_hour=100;assignment.db_insert()
 leave_type=frappe.db.get_single_value('DGII Payroll Settings','overtime_compensatory_leave_type')
 policy=frappe.get_doc({'doctype':'Overtime Pay Policy','title':'DEV rest rollback policy','company':employee.company,
  'valid_from':'2026-08-01','valid_until':'2026-09-23','approval_reference':'DEV synthetic equivalence; not a real approval',
  'weekly_threshold':68,'regular_percent':35,'extraordinary_percent':100,'night_percent':15,'weekly_rest_percent':100,'weekly_rest_cash':1,
  'night_basis':'Clock overlap','premium_combination':'Additive on base hour','enable_compensatory':1,'leave_type':leave_type,
  'hours_per_leave_day':8,'leave_increment':.5,'rest_hours_per_worked_hour':1,'weekly_rest_duration_hours':36,'weekly_rest_credit_hours':8})
 policy.insert(ignore_permissions=True);policy.flags.ignore_permissions=True;policy.submit()
 period=frappe.get_doc({'doctype':'Leave Period','name':prefix+'-PERIOD','company':employee.company,'from_date':'2026-01-01','to_date':'2026-12-31','is_active':1})
 period.insert(ignore_permissions=True)
 def punch(day,clock,kind):
  row=frappe.get_doc({'doctype':'Employee Checkin','employee':employee.name,'time':day+' '+clock,'log_type':kind,'skip_auto_attendance':0})
  row.insert(ignore_permissions=True);return row
 day=getdate('2026-08-31')
 while day<getdate('2026-09-06'):
  context=get_schedule_context(day,shift.name,base.holiday_list)
  if context['classification']=='Regular Workday':punch(str(day),'08:00:00','IN');punch(str(day),'18:00:00','OUT')
  day+=timedelta(days=1)
 punch('2026-09-06','07:00:00','IN');punch('2026-09-06','11:00:00','OUT')
 def source(method):
  doc=frappe.get_doc({'doctype':retro.DT,'employee':employee.name,'work_date':'2026-09-06',
   'authorization_start':'2026-09-06 07:00:00','authorization_end':'2026-09-06 11:00:00','maximum_hours':4,
   'reason':'DEV rest','exception_justification':'Synthetic historical exception','planned_settlement':method,
   'settlement_payroll_date':'2026-09-08','reconciliation_engine':retro.ENGINE})
  doc.insert(ignore_permissions=True);doc.flags.ignore_permissions=True;doc.submit()
  return doc,doc.name
 def choose(name,method):
  election=frappe.get_doc({'doctype':'Overtime Settlement Election','retroactive_adjustment':name,'choice':method,
   'employee_reference':'Synthetic employee election, rollback only','settlement_payroll_date':'2026-09-08','planned_start':'2026-09-08 18:00:00','planned_end':'2026-09-10 06:00:00'})
  election.insert(ignore_permissions=True);return election
 call,name=source('Compensatory Rest')
 with patch.object(evidence,'now_datetime',return_value=get_datetime('2026-09-06 20:00:00')):
  assert retro.get_status(name)['state']=='Verified'
  assert not frappe.db.get_value(retro.DT,name,'evidence_settlement_ready')
  election=choose(name,'Compensatory Rest')
  election.flags.ignore_permissions=True
  try:election.submit()
  except frappe.PermissionError:pass
  else:raise AssertionError('Generic submit bypassed managed approval')
  election.reload();duplicate=choose(name,'Compensatory Rest')
  invalid=frappe.get_doc({'doctype':'Overtime Settlement Election','authorization':base.name,'retroactive_adjustment':name,
    'choice':'Cash','employee_reference':'DEV invalid dual source'})
  try:invalid.insert(ignore_permissions=True)
  except frappe.ValidationError:pass
  else:raise AssertionError('Election accepted two source documents')
  frappe.db.savepoint('changed_before_choice')
  frappe.db.set_value('Employee Checkin',{'employee':employee.name,'time':'2026-09-06 11:00:00'},'time','2026-09-06 10:00:00')
  try:rest.approve_election(election.name)
  except frappe.ValidationError:pass
  else:raise AssertionError('Changed proof accepted for employee choice')
  frappe.db.rollback(save_point='changed_before_choice')
  rest.approve_election(election.name)
  try:rest.approve_election(duplicate.name)
  except frappe.ValidationError:pass
  else:raise AssertionError('Two active elections claimed the same authorization')
  frappe.db.savepoint('changed_before_credit')
  frappe.db.set_value('Employee Checkin',{'employee':employee.name,'time':'2026-09-06 11:00:00'},'time','2026-09-06 10:00:00')
  try:retro.create_compensatory_settlement(name)
  except frappe.ValidationError:pass
  else:raise AssertionError('Changed source created a retroactive credit')
  frappe.db.rollback(save_point='changed_before_credit')
  frappe.db.savepoint('wrong_credit_approver')
  frappe.db.set_value(retro.DT,name,'approver','Guest')
  try:retro.create_compensatory_settlement(name)
  except frappe.PermissionError:pass
  else:raise AssertionError('Unassigned user created a retroactive credit')
  frappe.db.rollback(save_point='wrong_credit_approver')
  from powerpro.controllers import overtime_settlement as settlement
  credit_before=frappe.db.count('Overtime Compensatory Credit');allocation_before=frappe.db.count('Leave Allocation')
  original_record=settlement._credit_and_record
  def fail_after_credit(doc):
   original_record(doc)
   raise RuntimeError('DEV injected after credit and allocation')
  with patch.object(settlement,'_credit_and_record',side_effect=fail_after_credit):
   try:retro.create_compensatory_settlement(name)
   except RuntimeError:pass
   else:raise AssertionError('Failure injection did not execute')
  assert frappe.db.count('Overtime Compensatory Credit')==credit_before
  assert frappe.db.count('Leave Allocation')==allocation_before
  assert frappe.db.get_value(retro.DT,name,'settlement_status')=='Pending'
  result=retro.create_compensatory_settlement(name)
  assert result['settlement_status']=='Credited' and result['retroactive_adjustment']==name and 'authorization' not in result,result
  auth=frappe.get_doc(retro.DT,name);election.reload()
  assert auth.verified_hours==4 and auth.compensatory_hours==8 and auth.compensatory_days==1
  assert election.status=='Credited' and election.minimum_rest_hours==36 and not election.leave_application
  assert frappe.db.get_value('Leave Allocation',auth.leave_allocation,'new_leaves_allocated')==1
  try:retro.create_compensatory_settlement(name)
  except frappe.ValidationError:pass
  else:raise AssertionError('Duplicate retroactive credit')
  assert frappe.db.count('Overtime Compensatory Credit',{'retroactive_adjustment':name,'docstatus':1})==1
  checks.append('four actual weekly-rest hours create one explicit eight-hour credit / one leave day, with 36 continuous hours still owed')
 def leave(day):
  doc=frappe.get_doc({'doctype':'Leave Application','employee':employee.name,'company':employee.company,'leave_type':leave_type,
   'from_date':day,'to_date':day,'posting_date':'2026-09-07','status':'Approved','leave_approver':'Administrator','follow_via_email':0,'description':'DEV rollback rest'})
  doc.insert(ignore_permissions=True);doc.flags.ignore_permissions=True;doc.submit();return doc
 application=leave('2026-09-09')
 frappe.db.savepoint('used_credit_cancel')
 try:
  call.reload();call.flags.ignore_permissions=True;call.cancel()
 except frappe.ValidationError:pass
 else:raise AssertionError('Source cancellation removed consumed leave balance')
 frappe.db.rollback(save_point='used_credit_cancel')
 assert frappe.db.get_value('Overtime Compensatory Credit',auth.compensatory_credit,'docstatus')==1
 assert frappe.db.get_value(rest.DT,election.name,'docstatus')==1

 from powerpro.controllers import checkin_overtime_review as review
 exit_name=frappe.db.get_value('Employee Checkin',{'employee':employee.name,'time':'2026-09-06 11:00:00'},'name')
 exit_doc=frappe.get_doc('Employee Checkin',exit_name)
 frappe.db.savepoint('used_credit_review')
 exit_doc.time='2026-09-06 10:00:00';exit_doc.save(ignore_permissions=True)
 reviewed=review.preview_review(name,'DEV measured three hours',source_type=retro.DT)
 try:review.apply_review(name,'DEV measured three hours',reviewed['token'],source_type=retro.DT)
 except frappe.ValidationError:pass
 else:raise AssertionError('Review reversed a consumed retroactive credit')
 assert frappe.db.get_value(rest.DT,election.name,'docstatus')==1
 assert frappe.db.get_value('Overtime Compensatory Credit',auth.compensatory_credit,'docstatus')==1
 frappe.db.rollback(save_point='used_credit_review');exit_doc.reload()
 rest.link_leave(election.name,application.name)
 with patch.object(rest,'now_datetime',return_value=get_datetime('2026-09-09 20:00:00')):
  try:rest.confirm_enjoyment(election.name,'2026-09-08 18:00:00','2026-09-10 06:00:00','Test confirmation')
  except frappe.ValidationError:pass
  else:raise AssertionError('Future rest was marked enjoyed')
 conflict=punch('2026-09-09','10:00:00','IN')
 with patch.object(rest,'now_datetime',return_value=get_datetime('2026-09-11 08:00:00')):
  try:rest.confirm_enjoyment(election.name,'2026-09-08 18:00:00','2026-09-10 06:00:00','Test confirmation')
  except frappe.ValidationError:pass
  else:raise AssertionError('Contradictory Checkin was ignored')
  conflict.time='2026-09-12 08:00:00';conflict.save(ignore_permissions=True)
  assert rest.confirm_enjoyment(election.name,'2026-09-08 18:00:00','2026-09-10 06:00:00','Synthetic HR verification')['status']=='Enjoyed'
  assert rest.confirm_enjoyment(election.name,'2026-09-08 18:00:00','2026-09-10 06:00:00','Synthetic HR verification')['status']=='Enjoyed'
  conflict.time='2026-09-09 10:00:00';conflict.save(ignore_permissions=True)
  assert rest.get_rest_status(election.name)['status']=='Review'
  conflict.time='2026-09-12 08:00:00';conflict.save(ignore_permissions=True)
 checks.append('native approved leave schedules rest; future confirmation and contradictory punches are rejected; explicit HR evidence confirms enjoyment')
 try:application.cancel()
 except frappe.ValidationError:pass
 else:raise AssertionError('Enjoyed leave was cancelled without correcting confirmation')
 assert frappe.db.get_value('Leave Application',application.name,'docstatus')==1
 rest.revoke_enjoyment(election.name,'Synthetic correction for cancellation proof')
 application.reload();application.flags.ignore_permissions=True;application.cancel()
 election.reload();assert not election.leave_application and election.status=='Credited'
 rest.reschedule(election.name,'2026-09-09 18:00:00','2026-09-11 06:00:00','Synthetic reschedule')
 with patch.object(rest,'now_datetime',return_value=get_datetime('2026-09-12 08:00:00')):
  assert rest.get_rest_status(election.name)['status']=='Overdue'
  from powerpro.power_pro.report.overtime_rest_follow_up.overtime_rest_follow_up import execute
  columns,rows,message=execute({'employee':employee.name})
  assert len(rows)==1 and rows[0]['status']=='Vencido: revisar disfrute' and rows[0]['retroactive_adjustment']==name
  assert len(execute({'employee':employee.name,'from_date':getdate('2026-09-11')})[1])==1
  assert not execute({'employee':employee.name,'from_date':'2026-09-12'})[1]
  assert len(execute({'employee':employee.name,'to_date':getdate('2026-09-11')})[1])==1
  assert not execute({'employee':employee.name,'to_date':'2026-09-10'})[1]
  try:execute({'employee':employee.name,'from_date':'2026-09-12','to_date':'2026-09-11'})
  except frappe.ValidationError:pass
  else:raise AssertionError('Inverted report dates were accepted')
  frozen_policy=frappe.parse_json(auth.evidence_snapshot)['input']['pay_policy']
  try:rest.validate_election(election,auth,frozen_policy,worked_hours=5,calculation={'weekly_rest_hours':4})
  except frappe.ValidationError as exc:assert 'mezcla descanso semanal' in str(exc)
  else:raise AssertionError('Mixed rest obligations silently lost nonweekly hours')
 checks.append('confirmed enjoyment requires an audited correction before native leave cancellation; cancelled leave restores pending scheduling and overdue status')
 # With the leave reversed, HR may revise physical work. The old election and
 # credit are released atomically and the employee must make a renewed choice.
 prior_credit=auth.compensatory_credit
 exit_doc.time='2026-09-06 10:00:00';exit_doc.save(ignore_permissions=True)
 reviewed=review.preview_review(name,'DEV measured three hours',source_type=retro.DT)
 review.apply_review(name,'DEV measured three hours',reviewed['token'],source_type=retro.DT)
 auth.reload();assert auth.verified_hours==3 and auth.settlement_status=='Pending' and not auth.compensatory_credit
 assert frappe.db.get_value('Overtime Compensatory Credit',prior_credit,'docstatus')==2
 election.reload();assert election.docstatus==2 and not election.active_authorization
 assert not auth.evidence_settlement_ready
 replacement=choose(name,'Compensatory Rest');rest.approve_election(replacement.name)
 retro.create_compensatory_settlement(name);auth.reload();election=replacement
 assert auth.compensatory_credit!=prior_credit and auth.compensatory_hours==8
 assert frappe.db.count('Overtime Compensatory Credit',{'retroactive_adjustment':name,'docstatus':1})==1
 checks.append('used leave blocks HR revision; after leave cancellation, measured three-hour review releases old credit/election and renewed choice creates exactly one replacement')
 call.reload();call.flags.ignore_permissions=True;call.cancel()
 assert frappe.db.get_value('Overtime Compensatory Credit',auth.compensatory_credit,'docstatus')==2
 election.reload();assert election.docstatus==2 and not election.active_authorization and not election.active_weekly_rest
 checks.append('source cancellation reverses the credit and releases the weekly-rest claim')
 assert frappe.db.get_value(retro.DT,name,'settlement_status')=='Cancelled'
 assert not frappe.db.count('Additional Salary',{'ref_doctype':retro.DT,'ref_docname':name,'docstatus':1})
 # An explicit cash election may replace a planned rest choice, with its own
 # payroll date and the existing native cash settlement guards.
 exit_doc.time='2026-09-06 11:00:00';exit_doc.save(ignore_permissions=True)
 cash,cash_name=source('Compensatory Rest')
 cash_election=choose(cash_name,'Cash')
 cash_election.settlement_payroll_date='2026-09-08';cash_election.save(ignore_permissions=True)
 rest.approve_election(cash_election.name)
 cash.reload();assert cash.planned_settlement=='Cash' and str(cash.settlement_payroll_date)=='2026-09-08'
 from powerpro.controllers.overtime_cash_settlement import create_cash_settlement
 result=create_cash_settlement(cash_name)
 cash.reload();assert cash.settlement_status=='Created' and cash.settlement_amount==800,result
 assert not frappe.db.count('Overtime Compensatory Credit',{'retroactive_adjustment':cash_name,'docstatus':1})
 cash.flags.ignore_permissions=True;cash.cancel()
 assert frappe.db.get_value(rest.DT,cash_election.name,'docstatus')==2
 checks.append('retroactive cash election carries its payroll date, creates cash once and releases its election on native cancellation')
 print(json.dumps({'checks':checks},ensure_ascii=False))
finally:
 frappe.db.rollback();frappe.db.commit=commit;frappe.enqueue=enqueue;frappe.sendmail=sendmail
 after={d:frappe.db.count(d) for d in types}
 assert before==after,(before,after)
 for dt,values in settings_before.items():assert values==frappe.db.get_singles_dict(dt),dt
 print(json.dumps({'rollback_counts':after,'settings_restored':True}))
 frappe.destroy()
