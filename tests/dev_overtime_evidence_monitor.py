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
 'User','Has Role','User Permission','Overtime Evidence Watch','Version','Error Log','Overtime Work Call','Overtime Authorization','Overtime Reconciliation Run','Ordinary Night Settlement','Additional Salary','Salary Slip']
before={d:frappe.db.count(d) for d in counts}
settings_before={d:frappe.db.get_singles_dict(d) for d in ['DGII Payroll Settings','Payroll Settings']}
commit,enqueue,sendmail=frappe.db.commit,frappe.enqueue,frappe.sendmail

def forbidden(*args,**kwargs):raise AssertionError('Commit or outbound effect forbidden')
frappe.db.commit=forbidden;frappe.enqueue=forbidden;frappe.sendmail=forbidden
prefix='EVIDENCE-WATCH-DEV-'+uuid.uuid4().hex[:8]
try:
 frappe.db.set_single_value('DGII Payroll Settings',{'enable_checkin_overtime_reconciliation':1,'checkin_overtime_effective_from':'2026-09-01',
  'enable_retroactive_overtime_adjustment':1,'retroactive_overtime_from_date':'2026-09-01','retroactive_overtime_to_date':'2026-09-30',
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
 from powerpro.controllers import overtime_evidence_monitor as monitor,checkin_overtime_review as review
 from powerpro.power_pro.report.overtime_evidence_follow_up.overtime_evidence_follow_up import execute
 assert monitor.check_source(DT,'does-not-exist')['status']=='Disabled'
 with patch.object(monitor,'_candidates',side_effect=AssertionError('Disabled monitor scanned sources')):monitor.scheduled_check()
 for day in ['2026-09-07','2026-09-08']:
  for clock,kind in [('08:00:00','IN'),('12:00:00','OUT'),('13:00:00','IN')]:punch(day,clock,kind)
 first_exit=punch('2026-09-07','20:00:00','OUT');punch('2026-09-08','20:00:00','OUT')
 first=draft('2026-09-07');first.submit();first.reload()
 second=draft('2026-09-08');second.submit();second.reload()
 originals={doc.name:doc.evidence_snapshot for doc in [first,second]}
 money_before=frappe.db.count('Additional Salary');punches_before=frappe.db.count('Employee Checkin')
 frappe.db.set_single_value('DGII Payroll Settings','enable_overtime_evidence_monitor',1)
 candidates=monitor._candidates();assert {r['name'] for r in candidates}=={first.name,second.name},candidates
 one=monitor.check_source(DT,first.name);two=monitor.check_source(DT,second.name)
 assert one['status']=='Current' and two['status']=='Current',(one,two)
 version_count=frappe.db.count('Version')
 assert not monitor.check_source(DT,first.name)['changed']
 assert frappe.db.count('Version')==version_count
 assert not monitor._candidates()
 assert not execute({'employee':employee.name})[1]
 assert len(execute({'employee':employee.name,'include_current':1})[1])==2
 # Changed prior punch makes both source and later real-week dependent visible.
 first_exit.time='2026-09-07 19:00:00';first_exit.save(ignore_permissions=True)
 one=monitor.check_source(DT,first.name);two=monitor.check_source(DT,second.name)
 assert one['status']=='Needs Review' and two['status']=='Needs Review'
 watch=frappe.get_doc(monitor.DT,one['name'])
 assert watch.stored_hours==2 and watch.current_hours==1 and watch.responsible=='Administrator'
 assert any(r['name']==second.name and r['blocks_reversal'] for r in frappe.parse_json(watch.dependencies))
 assert len(execute({'employee':employee.name})[1])==2
 watch.summary='Attempt to hide';watch.flags.ignore_permissions=True
 try:watch.save()
 except frappe.PermissionError:pass
 else:raise AssertionError('Generic edit changed the evidence incident')
 for doc in [first,second]:
  doc.reload();assert doc.evidence_snapshot==originals[doc.name] and doc.settlement_amount==280
 assert frappe.db.count('Additional Salary')==money_before and frappe.db.count('Employee Checkin')==punches_before
 # Monitoring remains useful when automatic creation is paused.
 frappe.db.set_single_value('DGII Payroll Settings','enable_checkin_overtime_reconciliation',0)
 assert monitor.recheck(one['name'])['status']=='Needs Review'
 frappe.db.set_single_value('DGII Payroll Settings','enable_checkin_overtime_reconciliation',1)
 second.flags.ignore_permissions=True;second.cancel()
 p=review.preview_review(first.name,'DEV correction after monitor',source_type=DT)
 review.apply_review(first.name,'DEV correction after monitor',p['token'],source_type=DT)
 current=monitor.recheck(one['name']);assert current['status']=='Current' and current['changed']
 watch.reload();assert watch.stored_hours==watch.current_hours==1
 # Age ordering checks the least recently examined source before a fresh row.
 frappe.db.set_value(monitor.DT,two['name'],'checked_on','2026-01-01 00:00:00')
 assert monitor._candidates(1)[0]['name']==second.name
 commits=[]
 with patch.object(frappe.db,'commit',side_effect=lambda:commits.append(True)):
  monitor.scheduled_check()
 assert len(commits)==1
 assert not monitor._candidates()
 # Computation errors are not reported as healthy and do not starve later rows.
 logged=[]
 with patch.object(monitor,'_evaluate',side_effect=RuntimeError('DEV injected engine failure')),patch.object(frappe,'log_error',side_effect=lambda **kw:logged.append(kw)):
  assert monitor.check_source(DT,first.name)['status']=='Error'
 assert len(logged)==1
 assert monitor.check_source(DT,first.name)['status']=='Current'
 # Independent ordinary night is watched without requiring a fake authorization.
 from powerpro.controllers import ordinary_night as night
 original_employee,original_assignment=employee,assignment
 evening=frappe.copy_doc(shift);evening.name=prefix+'-EVENING';evening.docstatus=0;evening.start_time='16:00:00';evening.end_time='23:00:00';evening.db_insert()
 employee=frappe.copy_doc(employee);employee.name=prefix+'-NIGHT-EMP';employee.docstatus=0;employee.default_shift=evening.name;employee.db_insert()
 assignment=frappe.copy_doc(assignment);assignment.name=prefix+'-NIGHT-SSA';assignment.docstatus=1;assignment.employee=employee.name;assignment.db_insert()
 punch('2026-09-07','16:00:00','IN');night_exit=punch('2026-09-07','23:00:00','OUT')
 night_doc=frappe.get_doc({'doctype':night.DT,'employee':employee.name,'work_date':'2026-09-07',
  'settlement_payroll_date':'2026-09-15','review_reference':'DEV monitored ordinary shift'})
 night_doc.insert(ignore_permissions=True);night_doc.flags.ignore_permissions=True;night_doc.submit()
 assert monitor.check_source(night.DT,night_doc.name)['status']=='Current'
 night_exit.time='2026-09-07 22:30:00';night_exit.save(ignore_permissions=True)
 assert monitor.check_source(night.DT,night_doc.name)['status']=='Needs Review'
 night_doc.reload();assert night_doc.settlement_amount==30
 night_doc.flags.ignore_permissions=True;night_doc.cancel()
 assert monitor.check_source(night.DT,night_doc.name)['status']=='Current'
 # Native Work Call creates an enrolled authorization, then late evidence makes
 # its saved work appear in the same follow-up queue.
 employee=frappe.copy_doc(original_employee);employee.name=prefix+'-AUTH-EMP';employee.docstatus=0;employee.db_insert()
 assignment=frappe.copy_doc(original_assignment);assignment.name=prefix+'-AUTH-SSA';assignment.docstatus=1;assignment.employee=employee.name;assignment.db_insert()
 punch('2026-09-14','08:00:00','IN');auth_exit=punch('2026-09-14','20:00:00','OUT')
 call=frappe.copy_doc(frappe.get_doc('Overtime Work Call','CONV-HE-2026-00004-1'));call.name=None;call.docstatus=0
 call.company=employee.company;call.from_date='2026-09-14';call.to_date='2026-09-14';call.planned_settlement='Cash'
 call.automation_mode='Verified Checkins';call.evidence_auto_settle=0
 call.set('employees',[]);call.append('employees',{'employee':employee.name})
 call.set('dates',[]);call.append('dates',{'work_date':'2026-09-14','start_time':'18:00:00','end_time':'20:00:00','requested_hours':2})
 call.insert(ignore_permissions=True);call.flags.ignore_permissions=True;call.submit()
 auth_name=frappe.db.get_value('Overtime Authorization',{'overtime_work_call':call.name},'name')
 with patch.object(evidence,'now_datetime',return_value=get_datetime('2026-09-14 21:00:00')):
  assert evidence.process_authorization(auth_name)=='Verified'
  assert monitor.check_source('Overtime Authorization',auth_name)['status']=='Current'
  auth_exit.time='2026-09-14 19:00:00';auth_exit.save(ignore_permissions=True)
  assert monitor.check_source('Overtime Authorization',auth_name)['status']=='Needs Review'
  auth=frappe.get_doc('Overtime Authorization',auth_name)
  assert auth.verified_hours==2 and auth.settlement_status=='Pending'
 call.reload();call.flags.ignore_permissions=True;call.cancel()
 employee,assignment=original_employee,original_assignment
 # Native Desk permissions keep the queue within the reader's employee scope.
 other=frappe.copy_doc(employee);other.name=prefix+'-OTHER';other.docstatus=0;other.db_insert()
 foreign=frappe.copy_doc(first);foreign.name=prefix+'-FOREIGN';foreign.employee=other.name;foreign.docstatus=1;foreign.db_insert()
 foreign_watch=monitor.check_source(DT,foreign.name)
 user_name=prefix.lower()+'@example.invalid'
 user=frappe.get_doc({'doctype':'User','name':user_name,'email':user_name,'first_name':'DEV Monitor Reader',
  'enabled':1,'user_type':'System User','send_welcome_email':0});user.db_insert()
 role=frappe.get_doc({'doctype':'Has Role','parent':user_name,'parenttype':'User','parentfield':'roles','role':'HR Manager'});role.db_insert()
 permission=frappe.get_doc({'doctype':'User Permission','user':user_name,'allow':'Employee','for_value':employee.name,'apply_to_all_doctypes':1});permission.db_insert()
 frappe.clear_cache(user=user_name)
 frappe.set_user(user_name)
 try:
  rows=frappe.get_list(monitor.DT,fields=['name','source_type','source_name','employee'])
  assert rows and all(r.employee==employee.name for r in rows),rows
  assert all(r.name!=foreign_watch['name'] for r in rows)
  assert not monitor.watch_permission(frappe.get_doc(monitor.DT,foreign_watch['name']),user=user_name)
  assert execute({'employee':employee.name,'include_current':1})[1]
 finally:frappe.set_user('Administrator')
 first.reload();first.flags.ignore_permissions=True;first.cancel()
 print('EVIDENCE_MONITOR: disabled no-op, source/dependent incident, original finances untouched, idempotent versioning, authoritative resolution, paused-payments monitoring, bounded oldest-first scheduler and visible failure passed')
finally:
 frappe.db.rollback();frappe.db.commit=commit;frappe.enqueue=enqueue;frappe.sendmail=sendmail
 after={d:frappe.db.count(d) for d in counts}
 assert before==after,(before,after)
 for dt,values in settings_before.items():assert values==frappe.db.get_singles_dict(dt),dt
 print('EVIDENCE_MONITOR_ROLLBACK',json.dumps(after))
 frappe.destroy()
