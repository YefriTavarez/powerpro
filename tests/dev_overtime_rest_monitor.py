"""DEV-only native credit/leave/election lifecycle acceptance. All data rolled back."""
import json,uuid
from datetime import timedelta
from unittest.mock import patch
import frappe
from frappe.utils import getdate,get_datetime
SITE='igcaribe.fortabs.com'
frappe.init(site=SITE);frappe.connect();frappe.set_user('Administrator')
assert frappe.local.site==SITE and frappe.conf.developer_mode
from powerpro.controllers import checkin_overtime as evidence,overtime_rest as rest
from powerpro.controllers.overtime import get_schedule_context
from powerpro.controllers.overtime_cash_settlement import _get_linked_additional_salaries
prefix='REST-WATCH-DEV-'+uuid.uuid4().hex[:10]
types=['Employee','Shift Type','Employee Checkin','Attendance','Overtime Authorization','Overtime Work Call',
       'Overtime Pay Policy','Overtime Settlement Election','Overtime Reconciliation Run','Overtime Compensatory Credit',
       'Overtime Rest Watch','Working Time Evidence Reference','Notification Log','Notification Settings','User','Has Role','User Permission','Version','Error Log','Leave Period','Leave Allocation','Leave Application','Leave Ledger Entry','Additional Salary','Salary Slip','Salary Structure Assignment']
before={d:frappe.db.count(d) for d in types}
settings_before={d:frappe.db.get_singles_dict(d) for d in ['DGII Payroll Settings','HR Settings','Payroll Settings']}
commit,enqueue,sendmail=frappe.db.commit,frappe.enqueue,frappe.sendmail
def forbidden(*a,**kw):raise AssertionError('Commit or outbound effect in rollback fixture')
frappe.db.commit=forbidden;frappe.enqueue=forbidden;frappe.sendmail=forbidden
checks=[]
try:
 frappe.db.set_single_value('DGII Payroll Settings',{'enable_checkin_overtime_reconciliation':1,'checkin_overtime_effective_from':'2026-09-01',
  'enable_overtime_compensatory_settlement':1,'overtime_auto_payroll_date_policy':'Work Date'})
 frappe.db.set_single_value('HR Settings','send_leave_notification',0)
 frappe.db.set_single_value('Payroll Settings','email_salary_slip_to_employee',0)
 base=frappe.get_doc('Overtime Authorization','AUT-HE-2026-00018')
 employee=frappe.copy_doc(frappe.get_doc('Employee',base.employee));employee.name=prefix+'-EMP';employee.docstatus=0
 employee.status='Active';employee.employee_name='DEV Rest';employee.user_id=None;employee.company_email=None;employee.personal_email=None
 shift=frappe.copy_doc(frappe.get_doc('Shift Type','Diurna Extendida'));shift.name=prefix+'-SHIFT';shift.docstatus=0;shift.enable_auto_attendance=0
 shift.determine_check_in_and_check_out='Alternating entries as IN and OUT during the same shift';shift.working_hours_calculation_based_on='Every Valid Check-in and Check-out'
 shift.last_sync_of_checkin='2026-09-30 23:00:00';shift.db_insert();employee.default_shift=shift.name;employee.db_insert()
 original=frappe.get_all('Salary Structure Assignment',filters={'employee':base.employee,'docstatus':1},pluck='name',order_by='from_date desc',limit=1)
 assignment=frappe.copy_doc(frappe.get_doc('Salary Structure Assignment',original[0]));assignment.name=prefix+'-SSA';assignment.employee=employee.name
 assignment.docstatus=1;assignment.from_date='2026-01-01';assignment.base=19064;assignment.salary_per_hour=100;assignment.db_insert()
 leave_type=frappe.db.get_single_value('DGII Payroll Settings','overtime_compensatory_leave_type')
 policy=frappe.get_doc({'doctype':'Overtime Pay Policy','title':'DEV rest rollback policy','company':employee.company,
  'valid_from':'2026-09-01','valid_until':'2026-09-30','approval_reference':'DEV synthetic equivalence; not a real approval',
  'weekly_threshold':68,'regular_percent':35,'extraordinary_percent':100,'night_percent':15,'weekly_rest_percent':100,'weekly_rest_cash':1,
  'night_basis':'Clock overlap','premium_combination':'Additive on base hour','enable_compensatory':1,'leave_type':leave_type,
  'hours_per_leave_day':8,'leave_increment':.5,'rest_hours_per_worked_hour':1,'weekly_rest_duration_hours':36,'weekly_rest_credit_hours':8})
 policy.insert(ignore_permissions=True);policy.flags.ignore_permissions=True;policy.submit()
 period=frappe.get_doc({'doctype':'Leave Period','name':prefix+'-PERIOD','company':employee.company,'from_date':'2026-01-01','to_date':'2026-12-31','is_active':1})
 period.insert(ignore_permissions=True)
 def punch(day,clock,kind):
  row=frappe.get_doc({'doctype':'Employee Checkin','employee':employee.name,'time':day+' '+clock,'log_type':kind,'skip_auto_attendance':0})
  row.insert(ignore_permissions=True);return row
 day=getdate('2026-09-07')
 while day<getdate('2026-09-13'):
  context=get_schedule_context(day,shift.name,base.holiday_list)
  if context['classification']=='Regular Workday':punch(str(day),'08:00:00','IN');punch(str(day),'18:00:00','OUT')
  day+=timedelta(days=1)
 punch('2026-09-13','07:00:00','IN');punch('2026-09-13','11:00:00','OUT')
 def source(method):
  call=frappe.copy_doc(frappe.get_doc('Overtime Work Call','CONV-HE-2026-00004-1'));call.name=None;call.docstatus=0
  call.company=employee.company;call.from_date='2026-09-13';call.to_date='2026-09-13';call.planned_settlement=method
  call.automation_mode='Verified Checkins';call.evidence_auto_settle=1
  call.set('employees',[]);call.append('employees',{'employee':employee.name})
  call.set('dates',[]);call.append('dates',{'work_date':'2026-09-13','start_time':'07:00:00','end_time':'11:00:00','requested_hours':4})
  from powerpro.power_pro.doctype.overtime_work_call import overtime_work_call
  from powerpro.power_pro.doctype.overtime_authorization import overtime_authorization
  with patch.object(overtime_work_call,'now_datetime',return_value=get_datetime('2026-09-12 12:00:00')), patch.object(overtime_authorization,'now_datetime',return_value=get_datetime('2026-09-12 12:00:00')):
   call.insert(ignore_permissions=True);call.flags.ignore_permissions=True;call.submit()
  return call,frappe.db.get_value('Overtime Authorization',{'overtime_work_call':call.name},'name')
 def choose(name,method):
  election=frappe.get_doc({'doctype':'Overtime Settlement Election','authorization':name,'choice':method,
   'employee_reference':'Synthetic employee election, rollback only','planned_start':'2026-09-15 18:00:00','planned_end':'2026-09-17 06:00:00'})
  election.insert(ignore_permissions=True);return election
 from powerpro.controllers import overtime_rest_monitor as monitor
 from contextlib import contextmanager,ExitStack
 @contextmanager
 def clock(date):
  with ExitStack() as stack:
   for module in [rest,evidence,monitor]:stack.enter_context(patch.object(module,'now_datetime',return_value=get_datetime(date)))
   yield
 def fails(fn,exc=frappe.ValidationError):
  try:fn()
  except exc:return
  raise AssertionError('Expected refusal')
 assert monitor.process_election('missing')['status']=='Disabled'
 with patch.object(monitor,'_candidates',side_effect=AssertionError('Disabled rest monitor scanned')):monitor.scheduled_check()
 call,name=source('Compensatory Rest')
 with clock('2026-09-14 12:00:00'):
  assert evidence.process_authorization(name)=='Verified'
  election=choose(name,'Compensatory Rest');rest.approve_election(election.name)
  frappe.db.set_single_value('DGII Payroll Settings',{'enable_overtime_rest_monitor':1,'enable_overtime_rest_notices':0,'overtime_rest_reminder_days':0})
  result=monitor.process_election(election.name);assert result['status']=='Approved'
  watch=frappe.get_doc(monitor.DT,result['name'])
  assert evidence.process_authorization(name)=='Frozen'
  auth=frappe.get_doc('Overtime Authorization',name);election.reload()
  before_source=auth.as_dict();before_election=election.as_dict();credit=frappe.get_doc('Overtime Compensatory Credit',auth.compensatory_credit)
  before_credit=credit.as_dict()
  assert monitor.process_election(election.name)['status']=='Credited'
  auth.reload();election.reload();credit.reload()
  assert auth.as_dict()==before_source and election.as_dict()==before_election and credit.as_dict()==before_credit
 # All actual notice records use a synthetic user and roll back; no email or
 # realtime network dispatch is allowed in this fixture.
 user_name=prefix.lower()+'@example.invalid'
 frappe.get_doc({'doctype':'User','name':user_name,'email':user_name,'first_name':'DEV Rest Reviewer',
  'enabled':1,'user_type':'System User','send_welcome_email':0}).db_insert()
 frappe.get_doc({'doctype':'Has Role','parent':user_name,'parenttype':'User','parentfield':'roles','role':'HR Manager'}).db_insert()
 permission=frappe.get_doc({'doctype':'User Permission','user':user_name,'allow':'Employee','for_value':employee.name,'apply_to_all_doctypes':1});permission.db_insert()
 frappe.get_doc({'doctype':'Notification Settings','name':user_name,'enabled':1,'enable_email_notifications':1,'seen':1}).db_insert()
 roles=frappe.db.get_single_value('DGII Payroll Settings','overtime_manual_verification_roles') or ''
 frappe.db.set_single_value('DGII Payroll Settings','overtime_manual_verification_roles',roles+'\nHR Manager');frappe.clear_cache(user=user_name)
 monitor.assign(watch.name,user_name,'Synthetic reviewer')
 frappe.db.set_single_value('DGII Payroll Settings','enable_overtime_rest_notices',1)
 emitted=[]
 real_rollback=frappe.db.rollback
 def sweep(fault=None):
  frappe.db.savepoint('rest_monitor_attempt');commits=[];errors=[]
  def rollback(*a,**kw):return real_rollback(*a,**kw) if a or kw else real_rollback(save_point='rest_monitor_attempt')
  with ExitStack() as stack:
   for p in [patch.object(monitor,'_candidates',return_value=[frappe._dict(name=election.name)]),
       patch.object(frappe.db,'commit',side_effect=lambda:commits.append(True)),patch.object(frappe.db,'rollback',side_effect=rollback),
       patch.object(frappe,'log_error',side_effect=lambda **kw:errors.append(kw))]:stack.enter_context(p)
   if fault:stack.enter_context(fault)
   monitor.scheduled_check()
  return commits,errors
 with patch.object(frappe,'publish_realtime',side_effect=lambda *a,**kw:emitted.append((a,kw))):
  with clock('2026-09-14 12:00:00'):
   notices=frappe.db.count('Notification Log')
   frappe.db.set_value('Notification Settings',user_name,'enabled',0)
   assert monitor.process_election(election.name)['notice_status']=='User muted'
   assert frappe.db.count('Notification Log')==notices
   frappe.db.set_value('Notification Settings',user_name,'enabled',1)
   assert monitor.process_election(election.name)['notice_status']=='Sent';watch.reload()
   log=frappe.get_doc('Notification Log',watch.last_notice)
   assert log.type=='Alert' and log.for_user==user_name and log.document_type==monitor.DT
   assert employee.name not in log.subject and auth.name not in log.subject
   assert frappe.db.count('Notification Log')==notices+1
   assert monitor.process_election(election.name)['notice_status']=='Unchanged'
   versions=frappe.db.count('Version');monitor.process_election(election.name)
   assert frappe.db.count('Version')==versions
   assert any(a==('notification',) and kw.get('after_commit') and kw.get('user')==user_name for a,kw in emitted)
   frappe.db.set_single_value('DGII Payroll Settings','overtime_rest_reminder_days',1)
   with clock('2026-09-15 11:59:59'):
    assert monitor.process_election(election.name)['notice_status']=='Unchanged'
   with clock('2026-09-15 12:00:00'):
    assert monitor.process_election(election.name)['notice_status']=='Sent'
   frappe.db.set_single_value('DGII Payroll Settings','overtime_rest_reminder_days',0)
   # Disabled reviewer is never impersonated or notified.
   frappe.db.set_value('User',user_name,'enabled',0);before_notices=frappe.db.count('Notification Log')
   commits,errors=sweep();watch.reload()
   assert watch.status=='Access Required' and not errors and frappe.db.count('Notification Log')==before_notices
   assert frappe.session.user=='Administrator'
   frappe.db.set_value('User',user_name,'enabled',1)
   watch.db_set('last_notice_key',None,update_modified=False)
   original_update=monitor._update
   def fail_after_notice(doc,values):
    if values.get('notice_status')=='Sent':raise RuntimeError('DEV fault after rest notice insert')
    return original_update(doc,values)
   commits,errors=sweep(patch.object(monitor,'_update',side_effect=fail_after_notice));watch.reload()
   assert watch.status=='Error' and len(errors)==1 and frappe.db.count('Notification Log')==before_notices and not watch.last_notice_key
   commits,errors=sweep();watch.reload()
   assert watch.status=='Credited' and watch.notice_status=='Sent' and not errors and frappe.db.count('Notification Log')==before_notices+1
  def leave(day):
   doc=frappe.get_doc({'doctype':'Leave Application','employee':employee.name,'company':employee.company,'leave_type':leave_type,
    'from_date':day,'to_date':day,'posting_date':'2026-09-14','status':'Approved','leave_approver':'Administrator','follow_via_email':0,'description':'DEV rest watch'})
   doc.insert(ignore_permissions=True);doc.flags.ignore_permissions=True;doc.submit();return doc
  application=leave('2026-09-16');rest.link_leave(election.name,application.name)
  with clock('2026-09-14 12:00:00'):
   assert monitor.process_election(election.name)['status']=='Scheduled'
  with clock('2026-09-18 12:00:00'):
   assert monitor.process_election(election.name)['status']=='Overdue'
   rest.confirm_enjoyment(election.name,'2026-09-15 18:00:00','2026-09-17 06:00:00','Synthetic confirmed rest')
   assert monitor.process_election(election.name)['status']=='Enjoyed'
   conflict=punch('2026-09-16','10:00:00','IN')
   assert monitor.process_election(election.name)['status']=='Review'
   watch.reload();assert any(i['code']=='checkin_during_confirmed_rest' for i in frappe.parse_json(watch.issues))
   # A reader cannot see evidence after a referenced checkin becomes hidden.
   restricted=frappe.get_doc({'doctype':'User Permission','user':user_name,'allow':'Employee Checkin',
    'for_value':conflict.name,'apply_to_all_doctypes':1});restricted.db_insert();frappe.clear_cache(user=user_name)
   frappe.set_user(user_name)
   try:
    assert not frappe.has_permission(monitor.DT,'read',doc=watch.name)
    assert not frappe.get_list(monitor.DT,filters={'name':watch.name},pluck='name')
   finally:frappe.set_user('Administrator')
   frappe.db.delete('User Permission',{'name':restricted.name});frappe.clear_cache(user=user_name)
   conflict.time='2026-09-19 08:00:00';conflict.save(ignore_permissions=True)
   assert monitor.process_election(election.name)['status']=='Enjoyed'
   # Broken live backing cannot continue displaying verified enjoyment.
   for dt,docname,field,bad,good,code in [
       ('Overtime Compensatory Credit',auth.compensatory_credit,'docstatus',2,1,'inactive_or_mismatched_credit'),
       ('Leave Allocation',auth.leave_allocation,'docstatus',2,1,'inactive_or_mismatched_allocation'),
       ('Leave Application',application.name,'status','Rejected','Approved','leave_no_longer_covers_rest')]:
    frappe.db.set_value(dt,docname,field,bad)
    assert monitor.process_election(election.name)['status']=='Review';watch.reload()
    assert any(i['code']==code for i in frappe.parse_json(watch.issues)),watch.issues
    assert frappe.db.get_value(dt,docname,field)==bad
    frappe.db.set_value(dt,docname,field,good)
    assert monitor.process_election(election.name)['status']=='Enjoyed'
   # Native correction, leave cancellation and source cancellation keep the
   # obligation visible until it is genuinely released.
   rest.revoke_enjoyment(election.name,'Synthetic correction')
   application.reload();application.flags.ignore_permissions=True;application.cancel()
   assert monitor.process_election(election.name)['status']=='Overdue'
   call.reload();call.flags.ignore_permissions=True;call.cancel()
   assert monitor.process_election(election.name)['status']=='Cancelled'
   assert rest.get_rest_status(election.name)['status']=='Cancelled'
   assert election.name not in [r.name for r in monitor._candidates()]
   watch.reload();assert watch.notice_status=='No action pending'
   watch.summary='Generic edit';watch.flags.ignore_permissions=True
   fails(lambda:watch.save(),frappe.PermissionError)
   fails(lambda:frappe.delete_doc(monitor.DT,watch.name,ignore_permissions=True),frappe.PermissionError)
 print('REST_MONITOR: native election/credit/leave/enjoyment lifecycle, contradictory punches and backing review, cancellation, internal notices, deduplication, permissions and atomic retry passed')
finally:
 frappe.set_user('Administrator');frappe.db.rollback();frappe.db.commit=commit;frappe.enqueue=enqueue;frappe.sendmail=sendmail
 after={d:frappe.db.count(d) for d in types};assert before==after,(before,after)
 for dt,values in settings_before.items():assert values==frappe.db.get_singles_dict(dt),dt
 print('REST_MONITOR_ROLLBACK',json.dumps(after));frappe.destroy()
