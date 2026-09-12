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
 'Working Time Review','Working Time Incident','Working Time Evidence Reference','Version','Error Log','User','Has Role','User Permission','Overtime Work Call','Overtime Authorization','Overtime Reconciliation Run','Ordinary Night Settlement','Additional Salary','Salary Slip']
before={d:frappe.db.count(d) for d in counts}
settings_before={d:frappe.db.get_singles_dict(d) for d in ['DGII Payroll Settings','Payroll Settings']}
commit,enqueue,sendmail=frappe.db.commit,frappe.enqueue,frappe.sendmail

def forbidden(*args,**kwargs):raise AssertionError('Commit or outbound effect forbidden')
frappe.db.commit=forbidden;frappe.enqueue=forbidden;frappe.sendmail=forbidden
prefix='WORK-REVIEWS-DEV-'+uuid.uuid4().hex[:8]
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
 from powerpro.controllers import working_time_incidents as cases,working_time_reviews as reviews,working_time_incident_monitor as monitor
 def fails(fn,exc=frappe.ValidationError):
  try:fn()
  except exc:return
  raise AssertionError('Expected refusal')
 for clock,kind in [('11:00:00','IN'),('15:00:00','OUT'),('16:00:00','IN'),('20:00:00','OUT')]:punch('2026-09-07',clock,kind)
 source=draft('2026-09-07');source.submit();source.reload();original=source.as_dict()
 initial=controls.preview(DT,source.name)
 assert next(c for c in initial['controls'] if c['code']=='daily_work')['status']==cases.CLEAR
 assert next(c for c in initial['controls'] if c['code']=='work_break')['status']==cases.CLEAR
 result=cases.record(DT,source.name,{},'Administrator',initial['input_hash'])
 review=frappe.get_doc(reviews.DT,frappe.get_doc(cases.DT,result[0]['name']).working_time_review)
 assert review.status=='Active' and review.registered_by=='Administrator'
 assert not frappe.db.exists(cases.DT,{'working_time_review':review.name,'control_code':'daily_work'})
 baseline=frappe.db.count(cases.DT);versions=frappe.db.count('Version')
 cases.record(DT,source.name,{},'Administrator',initial['input_hash'])
 assert frappe.db.count(cases.DT)==baseline and frappe.db.count(reviews.DT)==1 and frappe.db.count('Version')==versions
 assert reviews.process_review(review.name)['status']=='Disabled'
 with patch.object(reviews,'_candidates',side_effect=AssertionError('Disabled review scan')):reviews.scheduled_scan()
 # Contract: an explicitly saved scenario remains enrolled even when its
 # result has zero issues. Synthetic empty result does not certify compliance.
 from copy import deepcopy
 empty=deepcopy(initial);empty['controls']=[c for c in empty['controls'] if c['status']==cases.CLEAR]
 empty_options={'reference':'DEV empty-result registration contract'}
 with patch.object(controls,'preview',return_value=empty):
  assert not cases.record(DT,source.name,empty_options,'Administrator',empty['input_hash'])
 assert frappe.db.count(reviews.DT)==2
 other_review=frappe.get_doc(reviews.DT,frappe.db.get_value(reviews.DT,{'name':['!=',review.name]},'name'))
 reviews.configure(other_review.name,'Paused','Administrator','DEV contract case completed')
 # An already-approved source acquires new actual daily/break problems; keep
 # evidence and finances on the approved source unchanged.
 entry=frappe.get_doc('Employee Checkin',frappe.db.get_value('Employee Checkin',{'employee':employee.name,'time':'2026-09-07 11:00:00'},'name'))
 entry.time='2026-09-07 08:00:00';entry.save(ignore_permissions=True)
 frappe.db.set_single_value('DGII Payroll Settings','enable_working_time_incident_monitor',1)
 # Pausing a scenario prevents both discovery and notices on its existing cases.
 reviews.configure(review.name,'Paused','Administrator','DEV pause test')
 assert reviews.process_review(review.name)['status']=='Paused'
 assert monitor.process_incident(result[0]['name'])['status']=='Paused'
 assert not reviews._candidates() and not monitor._candidates()
 reviews.configure(review.name,'Active','Administrator','DEV resumed')
 # Full scheduler transaction failure after a new case insert must not leave
 # partial discovery. Savepoint substitution only keeps the fixture alive.
 real_rollback=frappe.db.rollback
 def scan(fault=None,full=False):
  frappe.db.savepoint('review_attempt');commits=[];logs=[]
  def rollback(*args,**kw):
   return real_rollback(*args,**kw) if args or kw else real_rollback(save_point='review_attempt')
  from contextlib import ExitStack
  with ExitStack() as stack:
   for p in [patch.object(reviews,'_candidates',return_value=[frappe._dict(name=review.name)]),
    patch.object(frappe.db,'commit',side_effect=lambda:commits.append(True)),patch.object(frappe.db,'rollback',side_effect=rollback),
    patch.object(frappe,'log_error',side_effect=lambda **kw:logs.append(kw))]:stack.enter_context(p)
   if fault:stack.enter_context(fault)
   monitor.scheduled_check() if full else reviews.scheduled_scan()
  return commits,logs
 original_update=cases._update
 def fail_after_new(doc,proof):
  r=original_update(doc,proof)
  if doc.control_code=='daily_work':raise RuntimeError('DEV failure after new incident insert')
  return r
 commits,logs=scan(patch.object(cases,'_update',side_effect=fail_after_new));review.reload()
 assert review.monitor_status=='Error' and len(logs)==1 and frappe.db.count(cases.DT)==baseline
 commits,logs=scan(full=True);review.reload()
 assert review.monitor_status=='Checked' and len(commits)>1 and all(commits) and not logs
 daily=frappe.get_doc(cases.DT,frappe.db.get_value(cases.DT,{'working_time_review':review.name,'control_code':'daily_work'},'name'))
 pause=frappe.get_doc(cases.DT,frappe.db.get_value(cases.DT,{'working_time_review':review.name,'control_code':'work_break'},'name'))
 assert daily.status=='Open' and daily.evaluation_status=='Review' and pause.evaluation_status=='Review'
 assert daily.monitor_status=='Needs Review' and daily.monitor_checked_on and pause.monitor_checked_on
 assert daily.responsible=='Administrator' and frappe.parse_json(daily.evaluation_options)['profile']=='General'
 count=frappe.db.count(cases.DT);versions=frappe.db.count('Version')
 reviews.process_review(review.name)
 assert frappe.db.count(cases.DT)==count and frappe.db.count('Version')==versions
 # Separate assignments: scenario owner controls new cases, existing delegated
 # cases retain their individual owner. The selected rule cannot be overwritten.
 user_name=prefix.lower()+'@example.invalid'
 frappe.get_doc({'doctype':'User','name':user_name,'email':user_name,'first_name':'DEV Review Owner','enabled':1,
  'user_type':'System User','send_welcome_email':0}).db_insert()
 frappe.get_doc({'doctype':'Has Role','parent':user_name,'parenttype':'User','parentfield':'roles','role':'HR Manager'}).db_insert()
 perm=frappe.get_doc({'doctype':'User Permission','user':user_name,'allow':'Employee','for_value':employee.name,'apply_to_all_doctypes':1});perm.db_insert()
 configured=frappe.db.get_single_value('DGII Payroll Settings','overtime_manual_verification_roles') or ''
 frappe.db.set_single_value('DGII Payroll Settings','overtime_manual_verification_roles',configured+'\nHR Manager');frappe.clear_cache(user=user_name)
 reviews.configure(review.name,'Active',user_name,'DEV owner for future cases')
 current=controls.preview(DT,source.name)
 fails(lambda:cases.record(DT,source.name,{},'Administrator',current['input_hash']))
 before_options=review.evaluation_options
 shift.last_sync_of_checkin='2026-09-07 14:00:00';shift.db_update()
 reviews.process_review(review.name);daily.reload()
 incomplete=frappe.get_doc(cases.DT,frappe.db.get_value(cases.DT,{'working_time_review':review.name,'control_code':'session_evidence'},'name'))
 assert incomplete.responsible==user_name and daily.responsible=='Administrator'
 review.reload();assert review.evaluation_options==before_options
 review.evaluation_options='{}';review.flags.ignore_permissions=True
 fails(lambda:review.save(),frappe.PermissionError)
 fails(lambda:frappe.delete_doc(reviews.DT,review.name,ignore_permissions=True),frappe.PermissionError)
 # Native list/direct access remain within Employee permissions.
 other=frappe.copy_doc(employee);other.name=prefix+'-OTHER';other.docstatus=0;other.db_insert()
 frappe.db.set_value('User Permission',perm.name,'for_value',other.name);frappe.clear_cache(user=user_name)
 frappe.set_user(user_name)
 try:
  assert not frappe.get_list(reviews.DT,filters={'name':review.name},pluck='name')
  assert not frappe.has_permission(reviews.DT,'read',doc=review.name)
 finally:frappe.set_user('Administrator')
 commits,logs=scan();review.reload();assert review.monitor_status=='Access Required' and not logs
 assert frappe.session.user=='Administrator'
 source.reload();assert source.as_dict()==original
 print('WORK_REVIEWS: explicit/empty enrollment, immutable scenario, new daily/break discovery, pause/resume, atomic retry, deduplication, configured future-case owner and native scope passed')
finally:
 frappe.set_user('Administrator');frappe.db.rollback();frappe.db.commit=commit;frappe.enqueue=enqueue;frappe.sendmail=sendmail
 after={d:frappe.db.count(d) for d in counts};assert before==after,(before,after)
 for dt,values in settings_before.items():assert values==frappe.db.get_singles_dict(dt),dt
 print('WORK_REVIEWS_ROLLBACK',json.dumps(after));frappe.destroy()
