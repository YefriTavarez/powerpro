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
 'Working Time Incident','Working Time Evidence Reference','Version','Error Log','User','Has Role','User Permission','Overtime Work Call','Overtime Authorization','Overtime Reconciliation Run','Ordinary Night Settlement','Additional Salary','Salary Slip']
before={d:frappe.db.count(d) for d in counts}
settings_before={d:frappe.db.get_singles_dict(d) for d in ['DGII Payroll Settings','Payroll Settings']}
commit,enqueue,sendmail=frappe.db.commit,frappe.enqueue,frappe.sendmail

def forbidden(*args,**kwargs):raise AssertionError('Commit or outbound effect forbidden')
frappe.db.commit=forbidden;frappe.enqueue=forbidden;frappe.sendmail=forbidden
prefix='WORK-INCIDENTS-DEV-'+uuid.uuid4().hex[:8]
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
 from powerpro.controllers import working_time_incidents as cases
 def fails(fn,exc=frappe.ValidationError):
  try:fn()
  except exc:return
  raise AssertionError('Expected refusal')
 for day in ['2026-09-07','2026-09-09']:
  for clock,kind in [('08:00:00','IN'),('12:00:00','OUT'),('13:00:00','IN'),('20:00:00','OUT')]:punch(day,clock,kind)
 first=draft('2026-09-07');first.submit();first.reload()
 second=draft('2026-09-09');second.submit();second.reload()
 source_before=first.as_dict();money_before=frappe.db.count('Additional Salary');checkins_before=frappe.db.count('Employee Checkin')
 opts={};result=controls.preview(DT,first.name)
 fails(lambda:cases.record(DT,first.name,opts,'Administrator','stale'))
 assert not frappe.db.count(cases.DT)
 rows=cases.record(DT,first.name,opts,'Administrator',result['input_hash'])
 assert len(rows)>=4
 records={frappe.get_doc(cases.DT,r['name']).control_code:r['name'] for r in rows}
 daily=frappe.get_doc(cases.DT,records['daily_work']);pause=frappe.get_doc(cases.DT,records['work_break'])
 assert daily.status=='Open' and daily.evaluation_status=='Review'
 versions=frappe.db.count('Version');count=frappe.db.count(cases.DT)
 assert all(not r['changed'] for r in cases.record(DT,first.name,opts,'Administrator',result['input_hash']))
 assert count==frappe.db.count(cases.DT) and versions==frappe.db.count('Version')
 fails(lambda:cases.resolve(daily.name,daily.evidence_hash,'Resolved','Not enough','DEV'))
 fails(lambda:cases.resolve(daily.name,daily.evidence_hash,'Documented Exception','','DEV'))
 cases.resolve(daily.name,daily.evidence_hash,'Documented Exception','DEV only exceptional work assessment','DEV reference')
 daily.reload();assert daily.status=='Documented Exception' and daily.resolved_by=='Administrator'
 resolved_hash=daily.resolved_hash
 # Repeated checks keep a decision for unchanged evidence and create no Version.
 versions=frappe.db.count('Version');assert not cases.recheck(daily.name)['changed'];assert versions==frappe.db.count('Version')
 # Changing another quarterly source must not reopen this daily decision.
 other_exit=frappe.get_doc('Employee Checkin',frappe.db.get_value('Employee Checkin',{'employee':employee.name,'time':'2026-09-09 20:00:00'},'name'))
 other_exit.time='2026-09-09 19:00:00';other_exit.save(ignore_permissions=True)
 assert not cases.recheck(daily.name)['changed'];daily.reload();assert daily.status=='Documented Exception'
 # Same session change reopens and retains the prior resolution/reference.
 for old,new in [('08:00:00','11:00:00'),('12:00:00','15:00:00'),('13:00:00','16:00:00')]:
  corrected=frappe.get_doc('Employee Checkin',frappe.db.get_value('Employee Checkin',{'employee':employee.name,'time':'2026-09-07 '+old},'name'))
  corrected.time='2026-09-07 '+new;corrected.save(ignore_permissions=True)
 cases.recheck(daily.name);daily.reload()
 assert daily.status=='Open' and daily.resolved_hash==resolved_hash and daily.resolution_reference=='DEV reference'
 assert daily.evaluation_status==cases.CLEAR,daily.evidence_snapshot
 fails(lambda:cases.resolve(daily.name,resolved_hash,'Resolved','Corrected marks','DEV correction'))
 cases.resolve(daily.name,daily.evidence_hash,'Resolved','Corrected complete session, eight hours','DEV correction')
 daily.reload();assert daily.status=='Resolved'
 versions=frappe.get_all('Version',filters={'ref_doctype':cases.DT,'docname':daily.name},pluck='data')
 assert any('Documented Exception' in row and 'Open' in row for row in versions)
 # A break case can close only after a fresh qualifying result.
 cases.recheck(pause.name);pause.reload();assert pause.evaluation_status==cases.CLEAR
 cases.resolve(pause.name,pause.evidence_hash,'Resolved','Four hours, one hour break, four hours','DEV evidence')
 quarter=frappe.get_doc(cases.DT,records['quarterly_extension'])
 cases.recheck(quarter.name);quarter.reload()
 fails(lambda:cases.resolve(quarter.name,quarter.evidence_hash,'Documented Exception','Cause still unclassified','DEV'))
 rest=frappe.get_doc(cases.DT,records['weekly_continuous_rest'])
 fails(lambda:cases.resolve(rest.name,rest.evidence_hash,'Documented Exception','No punches is not proof','DEV'))
 # Distinct regime evaluations have distinct cases, and do not overwrite General.
 alternate=dict(profile='Agreed industrial continuous day',reference='DEV agreement')
 r=controls.preview(DT,first.name,**alternate)
 alt=cases.record(DT,first.name,alternate,'Administrator',r['input_hash'])
 assert not set(x['name'] for x in alt).intersection(x['name'] for x in rows)
 daily.reload();assert daily.status=='Resolved' and frappe.parse_json(daily.evaluation_options)['profile']=='General'
 # Neither incident management nor a decision may rewrite the source or finance.
 first.reload();assert first.as_dict()==source_before
 assert frappe.db.count('Additional Salary')==money_before and frappe.db.count('Employee Checkin')==checkins_before
 daily.status='Open';daily.flags.ignore_permissions=True
 fails(lambda:daily.save(),frappe.PermissionError)
 fails(lambda:frappe.delete_doc(cases.DT,daily.name,ignore_permissions=True),frappe.PermissionError)
 # Native user/Employee scope applies to list, direct read, responsibility and action.
 other=frappe.copy_doc(employee);other.name=prefix+'-OTHER';other.docstatus=0;other.db_insert()
 foreign=frappe.copy_doc(first);foreign.name=prefix+'-FOREIGN';foreign.employee=other.name;foreign.docstatus=1;foreign.db_insert()
 foreign_case=frappe.copy_doc(frappe.get_doc(cases.DT,daily.name));foreign_case.name=prefix+'-CASE';foreign_case.employee=other.name
 foreign_case.docstatus=0;foreign_case.source_name=foreign.name;foreign_case.incident_key=prefix+'-FOREIGN';foreign_case.db_insert()
 user_name=prefix.lower()+'@example.invalid'
 user=frappe.get_doc({'doctype':'User','name':user_name,'email':user_name,'first_name':'DEV Incident Reviewer',
  'enabled':1,'user_type':'System User','send_welcome_email':0});user.db_insert()
 frappe.get_doc({'doctype':'Has Role','parent':user_name,'parenttype':'User','parentfield':'roles','role':'HR Manager'}).db_insert()
 frappe.get_doc({'doctype':'User Permission','user':user_name,'allow':'Employee','for_value':employee.name,'apply_to_all_doctypes':1}).db_insert()
 frappe.clear_cache(user=user_name)
 fails(lambda:cases.assign(daily.name,user_name,'Missing verification role'),frappe.PermissionError)
 configured=frappe.db.get_single_value('DGII Payroll Settings','overtime_manual_verification_roles') or ''
 frappe.db.set_single_value('DGII Payroll Settings','overtime_manual_verification_roles',configured+'\nHR Manager')
 cases.assign(daily.name,user_name,'DEV responsibility assigned')
 daily.reload();assert daily.responsible==user_name
 fails(lambda:cases.assign(foreign_case.name,user_name,'Hidden employee'),frappe.PermissionError)
 frappe.set_user(user_name)
 try:
  visible=frappe.get_list(cases.DT,fields=['name','employee'])
  assert visible and all(r.employee==employee.name for r in visible)
  assert not cases.incident_permission(foreign_case,user=user_name)
  fails(lambda:cases.recheck(foreign_case.name),frappe.PermissionError)
  assert cases.recheck(daily.name)['name']==daily.name
  # Parent access alone cannot disclose a stored reference hidden by native permissions.
  frappe.set_user('Administrator')
  restricted=frappe.get_doc({'doctype':'User Permission','user':user_name,'allow':'Employee Checkin',
   'for_value':other_exit.name,'apply_to_all_doctypes':1});restricted.db_insert()
  frappe.clear_cache(user=user_name);frappe.set_user(user_name)
  assert not frappe.has_permission(cases.DT,'read',doc=daily.name)
  assert not frappe.get_list(cases.DT,filters={'name':daily.name},pluck='name')
  fails(lambda:cases.recheck(daily.name),frappe.PermissionError)
 finally:frappe.set_user('Administrator')
 # Cancellation keeps an unresolved historical case; does not erase the work.
 first.reload();first.flags.ignore_permissions=True;first.cancel()
 cases.recheck(daily.name);daily.reload()
 assert daily.status=='Open' and daily.evaluation_status=='Historical review required' and daily.resolution_reference=='DEV correction'
 fails(lambda:cases.resolve(daily.name,daily.evidence_hash,'Resolved','Cancelled payment','DEV'))
 print('WORK_INCIDENTS: idempotency, token binding, audit, scoped reopening, guarded resolution, separate scenarios, no financial changes, native permissions and cancellation passed')
finally:
 frappe.set_user('Administrator');frappe.db.rollback();frappe.db.commit=commit;frappe.enqueue=enqueue;frappe.sendmail=sendmail
 after={d:frappe.db.count(d) for d in counts};assert before==after,(before,after)
 for dt,values in settings_before.items():assert values==frappe.db.get_singles_dict(dt),dt
 print('WORK_INCIDENTS_ROLLBACK',json.dumps(after));frappe.destroy()
