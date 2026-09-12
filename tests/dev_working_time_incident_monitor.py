"""DEV-only common-engine retroactive lifecycle; all test writes rolled back."""
import json,uuid
from unittest.mock import patch
import frappe
from frappe.utils import get_datetime
frappe.init(site='igcaribe.fortabs.com');frappe.connect();frappe.set_user('Administrator')
assert frappe.local.site=='igcaribe.fortabs.com' and frappe.conf.developer_mode
from powerpro.controllers import checkin_overtime as evidence,retroactive_evidence as retro
from powerpro.controllers.overtime import get_retroactive_adjustment_preview
from powerpro.controllers.overtime_cash_settlement import _get_linked_additional_salaries
DT=retro.DT
counts=['Employee','Shift Type','Employee Checkin','Salary Structure Assignment','Overtime Pay Policy',DT,
 'Working Time Review','Working Time Incident','Working Time Evidence Reference','Notification Log','Notification Settings','Version','Error Log','User','Has Role','User Permission','Overtime Work Call','Overtime Authorization','Overtime Reconciliation Run','Ordinary Night Settlement','Additional Salary','Salary Slip']
before={d:frappe.db.count(d) for d in counts}
settings_before={d:frappe.db.get_singles_dict(d) for d in ['DGII Payroll Settings','Payroll Settings']}
commit,enqueue,sendmail=frappe.db.commit,frappe.enqueue,frappe.sendmail

def forbidden(*args,**kwargs):raise AssertionError('Commit or outbound effect forbidden')
frappe.db.commit=forbidden;frappe.enqueue=forbidden;frappe.sendmail=forbidden
prefix='INCIDENT-MONITOR-DEV-'+uuid.uuid4().hex[:8]
try:
 frappe.db.set_single_value('DGII Payroll Settings',{'enable_checkin_overtime_reconciliation':1,'checkin_overtime_effective_from':'2026-09-01',
  'enable_manual_overtime_verification':1,'enable_retroactive_overtime_adjustment':1,'retroactive_overtime_from_date':'2026-09-01','retroactive_overtime_to_date':'2026-09-30',
  'retroactive_overtime_submission_deadline':'2026-09-30'})
 frappe.db.set_single_value('Payroll Settings','email_salary_slip_to_employee',0)
 base=frappe.get_doc('Overtime Authorization','AUT-HE-2026-00018')
 shift=frappe.copy_doc(frappe.get_doc('Shift Type','Diurna Extendida'));shift.name=prefix+'-SHIFT';shift.docstatus=0
 shift.start_time='08:00:00';shift.end_time='18:00:00';shift.enable_auto_attendance=0
 shift.begin_check_in_before_shift_start_time=0;shift.allow_check_out_after_shift_end_time=0
 shift.determine_check_in_and_check_out='Alternating entries as IN and OUT during the same shift'
 shift.working_hours_calculation_based_on='Every Valid Check-in and Check-out';shift.last_sync_of_checkin='2026-09-30 23:00:00';shift.db_insert()
 employee=frappe.copy_doc(frappe.get_doc('Employee',base.employee));employee.name=prefix+'-EMP';employee.docstatus=0
 employee.employee_name='DEV Retroactive Evidence';employee.user_id=None;employee.company_email=None;employee.personal_email=None
 employee.default_shift=shift.name;employee.overtime_approver='Administrator';employee.status='Active';employee.db_insert()
 name=frappe.get_all('Salary Structure Assignment',filters={'employee':base.employee,'docstatus':1},pluck='name',order_by='from_date desc',limit=1)[0]
 assignment=frappe.copy_doc(frappe.get_doc('Salary Structure Assignment',name));assignment.name=prefix+'-SSA';assignment.employee=employee.name
 assignment.docstatus=1;assignment.from_date='2026-01-01';assignment.base=19064;assignment.salary_per_hour=100;assignment.db_insert()
 policy=frappe.get_doc({'doctype':'Overtime Pay Policy','title':prefix,'company':employee.company,
  'valid_from':'2026-09-01','valid_until':'2026-09-30','approval_reference':'Synthetic40% DEV policy, not actual approval',
  'weekly_threshold':68,'regular_percent':40,'extraordinary_percent':100,'night_percent':15,'weekly_rest_percent':100,
  'night_basis':'Clock overlap','premium_combination':'Additive on base hour'})
 policy.insert(ignore_permissions=True);policy.flags.ignore_permissions=True;policy.submit()
 def punch(day,clock,kind):
  row=frappe.get_doc({'doctype':'Employee Checkin','employee':employee.name,'time':day+' '+clock,'log_type':kind})
  row.insert(ignore_permissions=True);return row
 def draft(day,start='18:00:00',end='20:00:00',maximum=2):
  doc=frappe.get_doc({'doctype':DT,'employee':employee.name,'work_date':day,'authorization_start':day+' '+start,
   'authorization_end':day+' '+end,'maximum_hours':maximum,'reason':'DEV historical work','exception_justification':'DEV historical exception',
   'planned_settlement':'Cash','settlement_payroll_date':'2026-09-15','reconciliation_engine':retro.ENGINE})
  doc.insert(ignore_permissions=True);doc.flags.ignore_permissions=True;return doc
 from powerpro.controllers import working_time_controls as controls
 from powerpro.controllers import working_time_incidents as cases,working_time_incident_monitor as monitor
 from frappe.utils import now_datetime
 from datetime import timedelta
 def fails(fn,exc=frappe.ValidationError):
  try:fn()
  except exc:return
  raise AssertionError('Expected refusal')
 assert monitor.process_incident('missing')['status']=='Disabled'
 with patch.object(monitor,'_candidates',side_effect=AssertionError('Disabled monitor scanned cases')):monitor.scheduled_check()
 fails(lambda:monitor.validate_settings(frappe._dict(enable_working_time_incident_notices=1,enable_working_time_incident_monitor=0)))
 for value in [-1,31,1.5,'nan','inf']:
  fails(lambda:monitor.validate_settings(frappe._dict(working_time_incident_reminder_days=value)))
 for clock,kind in [('08:00:00','IN'),('12:00:00','OUT'),('13:00:00','IN'),('20:00:00','OUT')]:punch('2026-09-07',clock,kind)
 source=draft('2026-09-07');source.submit();source.reload();saved=source.as_dict()
 user_name=prefix.lower()+'@example.invalid'
 frappe.get_doc({'doctype':'User','name':user_name,'email':user_name,'first_name':'DEV Incident Monitor',
  'enabled':1,'user_type':'System User','send_welcome_email':0}).db_insert()
 frappe.get_doc({'doctype':'Has Role','parent':user_name,'parenttype':'User','parentfield':'roles','role':'HR Manager'}).db_insert()
 frappe.get_doc({'doctype':'User Permission','user':user_name,'allow':'Employee','for_value':employee.name,'apply_to_all_doctypes':1}).db_insert()
 preferences=frappe.get_doc({'doctype':'Notification Settings','name':user_name,'enabled':1,'enable_email_notifications':1,'seen':1});preferences.db_insert()
 roles=frappe.db.get_single_value('DGII Payroll Settings','overtime_manual_verification_roles') or ''
 frappe.db.set_single_value('DGII Payroll Settings','overtime_manual_verification_roles',roles+'\nHR Manager')
 frappe.clear_cache(user=user_name)
 options={'rest_start':'2026-09-08 00:00:00','rest_end':'2026-09-09 12:00:00'}
 result=controls.preview(DT,source.name,**options)
 registered=cases.record(DT,source.name,options,user_name,result['input_hash'])
 docs={frappe.get_doc(cases.DT,r['name']).control_code:frappe.get_doc(cases.DT,r['name']) for r in registered}
 daily,rest=docs['daily_work'],docs['weekly_continuous_rest']
 cases.resolve(daily.name,daily.evidence_hash,'Documented Exception','DEV synthetic exceptional assessment','DEV only')
 daily.reload();original_resolution=daily.resolved_hash
 notices_before=frappe.db.count('Notification Log');money_before=frappe.db.count('Additional Salary')
 frappe.db.set_single_value('DGII Payroll Settings',{'enable_working_time_incident_monitor':1,'enable_working_time_incident_notices':1,'working_time_incident_reminder_days':7})
 emitted=[]
 with patch.object(frappe,'publish_realtime',side_effect=lambda *args,**kw:emitted.append((args,kw))):
  # Closed cases are included; unchanged decisions do not send notices.
  assert daily.name in [r.name for r in monitor._candidates()]
  assert monitor.process_incident(daily.name)['notice_status']=='No open case'
  assert frappe.db.count('Notification Log')==notices_before
  exit_doc=frappe.get_doc('Employee Checkin',frappe.db.get_value('Employee Checkin',{'employee':employee.name,'time':'2026-09-07 20:00:00'},'name'))
  exit_doc.time='2026-09-07 19:00:00';exit_doc.save(ignore_permissions=True)
  assert monitor.process_incident(daily.name)['notice_status']=='Sent'
  daily.reload();assert daily.status=='Open' and daily.resolved_hash==original_resolution
  log=frappe.get_doc('Notification Log',daily.last_notice)
  assert log.type=='Alert' and log.for_user==user_name and log.document_name==daily.name
  assert employee.name not in log.subject and source.name not in log.subject
  assert frappe.session.user=='Administrator' and frappe.db.count('Notification Log')==notices_before+1
  assert any(a==('notification',) and kw.get('after_commit') and kw.get('user')==user_name for a,kw in emitted)
  assert monitor.process_incident(daily.name)['notice_status']=='Unchanged'
  versions=frappe.db.count('Version');monitor.process_incident(daily.name)
  assert frappe.db.count('Version')==versions and frappe.db.count('Notification Log')==notices_before+1
  # No notice when muted; turning notifications back on preserves delivery.
  frappe.db.set_value('Notification Settings',user_name,'enabled',0)
  assert monitor.process_incident(rest.name)['notice_status']=='User muted'
  frappe.db.set_value('Notification Settings',user_name,'enabled',1)
  assert monitor.process_incident(rest.name)['notice_status']=='Sent';rest.reload()
  log=frappe.get_doc('Notification Log',rest.last_notice)
  assert 'Descanso previsto vencido' in log.subject
  assert rest.status=='Open' and rest.evaluation_status=='Enjoyment unverified'
  # Future clocks exercise reminder boundaries without changing work evidence.
  next_time=get_datetime(daily.last_notice_on)+timedelta(days=7)
  with patch.object(monitor,'now_datetime',return_value=next_time-timedelta(seconds=1)):
   assert monitor.process_incident(daily.name)['notice_status']=='Unchanged'
  with patch.object(monitor,'now_datetime',return_value=next_time):
   assert monitor.process_incident(daily.name)['notice_status']=='Sent'
  frappe.db.set_single_value('DGII Payroll Settings','working_time_incident_reminder_days',0)
  with patch.object(monitor,'now_datetime',return_value=next_time+timedelta(days=30)):
   assert monitor.process_incident(daily.name)['notice_status']=='Unchanged'
  frappe.db.set_single_value('DGII Payroll Settings','enable_working_time_incident_notices',0)
  assert monitor.process_incident(rest.name)['notice_status']=='Disabled'
  frappe.db.set_single_value('DGII Payroll Settings','enable_working_time_incident_notices',1)
  # Scheduler errors rollback the entire attempt, then persist an operational
  # error only. Test savepoint preserves the enclosing synthetic fixture.
  real_rollback=frappe.db.rollback
  def sweep(name,fault=None):
   frappe.db.savepoint('monitor_attempt');commits=[];logs=[]
   def rollback(*args,**kw):
    if args or kw:return real_rollback(*args,**kw)
    return real_rollback(save_point='monitor_attempt')
   from powerpro.controllers import working_time_reviews as reviews
   patches=[patch.object(reviews,'scheduled_scan'),patch.object(monitor,'_candidates',return_value=[frappe._dict(name=name)]),
    patch.object(frappe.db,'commit',side_effect=lambda:commits.append(True)),
    patch.object(frappe.db,'rollback',side_effect=rollback),patch.object(frappe,'log_error',side_effect=lambda **kw:logs.append(kw))]
   from contextlib import ExitStack
   with ExitStack() as stack:
    for p in patches:stack.enter_context(p)
    if fault:stack.enter_context(fault)
    monitor.scheduled_check()
   return commits,logs
  # A disabled responsible person cannot be impersonated or notified.
  frappe.db.set_value('User',user_name,'enabled',0)
  old_notices=frappe.db.count('Notification Log')
  commits,logs=sweep(daily.name);daily.reload()
  assert daily.monitor_status=='Access Required' and commits==[True] and not logs
  assert frappe.db.count('Notification Log')==old_notices and frappe.session.user=='Administrator'
  frappe.db.set_value('User',user_name,'enabled',1)
  # A revoked Employee scope also prevents recheck and delivery.
  other=frappe.copy_doc(employee);other.name=prefix+'-OTHER';other.docstatus=0;other.db_insert()
  permission_name=frappe.db.get_value('User Permission',{'user':user_name,'allow':'Employee'},'name')
  frappe.db.set_value('User Permission',permission_name,'for_value',other.name);frappe.clear_cache(user=user_name)
  commits,logs=sweep(daily.name);daily.reload()
  assert daily.monitor_status=='Access Required' and not logs and frappe.db.count('Notification Log')==old_notices
  frappe.db.set_value('User Permission',permission_name,'for_value',employee.name);frappe.clear_cache(user=user_name)
  # A failure after Notification Log insert also rolls back that log and its
  # deduplication fields. Retrying delivers exactly once.
  cases.assign(daily.name,'Administrator','DEV reassignment for notification test')
  # No processing occurs between assignments; every delivered notice targets the synthetic user.
  cases.assign(daily.name,user_name,'DEV reassignment restored')
  daily.reload();daily.db_set('last_notice_key',None,update_modified=False)
  old_key=daily.last_notice_key;old_notices=frappe.db.count('Notification Log')
  original_save=monitor._save_state
  def fail_after_notice(doc,values):
   if values.get('notice_status')=='Sent':raise RuntimeError('DEV failure after notification insert')
   return original_save(doc,values)
  commits,logs=sweep(daily.name,patch.object(monitor,'_save_state',side_effect=fail_after_notice));daily.reload()
  assert daily.monitor_status=='Error' and len(logs)==1
  assert frappe.db.count('Notification Log')==old_notices and daily.last_notice_key==old_key
  commits,logs=sweep(daily.name);daily.reload()
  assert daily.monitor_status=='Needs Review' and daily.notice_status=='Sent' and not logs
  assert frappe.db.count('Notification Log')==old_notices+1
  assert daily.name not in [r.name for r in monitor._candidates()]
  frappe.db.set_value(cases.DT,daily.name,'monitor_checked_on','2026-01-01 00:00:00')
  # Every test case has now been checked once so the oldest is unambiguous.
  for d in docs.values():
   if d.name!=daily.name:frappe.db.set_value(cases.DT,d.name,'monitor_checked_on',now_datetime())
  assert monitor._candidates(1)[0].name==daily.name
 source.reload();assert source.as_dict()==saved
 assert frappe.db.count('Additional Salary')==money_before
 print('INCIDENT_MONITOR: default-off, closed-case reopening, native internal alerts without email, permission/active-user checks, mute, deduplication, exact reminder boundary, overdue-rest wording, transactional retry, bounded scheduler and unchanged finance passed')
finally:
 frappe.set_user('Administrator');frappe.db.rollback();frappe.db.commit=commit;frappe.enqueue=enqueue;frappe.sendmail=sendmail
 after={d:frappe.db.count(d) for d in counts};assert before==after,(before,after)
 for dt,values in settings_before.items():assert values==frappe.db.get_singles_dict(dt),dt
 print('INCIDENT_MONITOR_ROLLBACK',json.dumps(after));frappe.destroy()
