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
counts=['Employee','Shift Type','Employee Checkin','Overtime Authorization','Overtime Work Call','Overtime Reconciliation Run','Overtime Pay Policy',DT,'Additional Salary','Salary Slip','Salary Structure Assignment','Ordinary Night Automation','Ordinary Night Automation Day','Error Log','User','Has Role','User Permission','Version']
before={dt:frappe.db.count(dt) for dt in counts}
settings_before={dt:frappe.db.get_singles_dict(dt) for dt in ['DGII Payroll Settings','Payroll Settings']}
commit,enqueue,sendmail=frappe.db.commit,frappe.enqueue,frappe.sendmail

def forbidden(*a,**kw):raise AssertionError('Commit or outbound effect forbidden')
frappe.db.commit=forbidden;frappe.enqueue=forbidden;frappe.sendmail=forbidden
prefix='NIGHT-AUTO-DEV-'+uuid.uuid4().hex[:8]
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
  'night_basis':'Clock overlap','premium_combination':'Additive on base hour','enable_compensatory':0,'auto_ordinary_night':1})
 policy.insert(ignore_permissions=True);policy.flags.ignore_permissions=True;policy.submit()
 def punch(stamp,kind):
  doc=frappe.get_doc({'doctype':'Employee Checkin','employee':employee.name,'time':stamp,'log_type':kind});doc.insert(ignore_permissions=True);return doc
 from powerpro.controllers import ordinary_night_automation as auto
 def schedule(**kwargs):
  doc=frappe.get_doc({'doctype':auto.DT,'employee':employee.name,'from_date':'2026-09-14','to_date':'2026-09-14',
   'settlement_payroll_date':'2026-09-15','policy':policy.name,'reference':'DEV explicit independent enrollment',**kwargs})
  doc.insert(ignore_permissions=True);doc.flags.ignore_permissions=True;return doc
 def reject(fn):
  try:fn()
  except (frappe.ValidationError,frappe.PermissionError):return
  raise AssertionError('Expected rejection')
 with patch.object(night,'now_datetime',return_value=get_datetime('2026-09-16 10:00:00')),patch.object(auto,'now_datetime',return_value=get_datetime('2026-09-16 10:00:00')):
  doc=schedule();assert not doc.enabled and len(doc.days)==1
  doc.submit();assert auto.process_day(doc.name,'2026-09-14')['status']=='Paused'
  doc.reload();doc.enabled=1;doc.save()
  frappe.db.set_single_value('DGII Payroll Settings','enable_checkin_overtime_reconciliation',0)
  with patch.object(auto,'_candidates',side_effect=AssertionError('Disabled scanner queried')):auto.scheduled_check()
  assert auto.process_day(doc.name,'2026-09-14')['status']=='Disabled'
  frappe.db.set_single_value('DGII Payroll Settings','enable_checkin_overtime_reconciliation',1)
  duplicate=schedule(enabled=1);reject(duplicate.submit)
  assert len(auto._candidates())==1
  first=punch('2026-09-14 18:00:00','IN')
  result=auto.process_day(doc.name,'2026-09-14');assert result['status']=='Needs Review',result
  assert frappe.db.count(DT)==before[DT]
  last=punch('2026-09-15 02:00:00','OUT')
  shift.db_set('last_sync_of_checkin','2026-09-14 20:00:00')
  result=auto.process_day(doc.name,'2026-09-14');assert result['status']=='Waiting',result
  shift.db_set('last_sync_of_checkin','2026-09-30 23:00:00')
  amounts=frappe.db.count('Additional Salary');original=auto._evaluate
  def fail_after_creation(*args,**kwargs):
   original(*args,**kwargs)
   raise RuntimeError('DEV injected post-cash failure')
  logged=[]
  with patch.object(auto,'_evaluate',side_effect=fail_after_creation),patch.object(frappe,'log_error',side_effect=lambda **kw:logged.append(kw)):
   result=auto.process_day(doc.name,'2026-09-14');assert result['status']=='Error',result
  assert logged and 'DEV injected post-cash failure' in logged[0]['message']
  assert frappe.db.count(DT)==before[DT] and frappe.db.count('Additional Salary')==amounts
  setter=frappe.db.set_value
  def fail_day_write(dt,*args,**kwargs):
   if dt==auto.DAY:raise RuntimeError('DEV final daily record failure')
   return setter(dt,*args,**kwargs)
  with patch.object(frappe.db,'set_value',side_effect=fail_day_write):
   try:auto.process_day(doc.name,'2026-09-14')
   except RuntimeError:pass
   else:raise AssertionError('Daily write failure did not run')
  assert frappe.db.count(DT)==before[DT] and frappe.db.count('Additional Salary')==amounts
  result=auto.process_day(doc.name,'2026-09-14');assert result['status']=='Created' and result['amount']==75,result
  settled=frappe.get_doc(DT,result['settlement']);assert settled.docstatus==1 and settled.night_hours==5
  assert not auto._candidates()
  assert auto.process_day(doc.name,'2026-09-14')['settlement']==settled.name
  assert frappe.db.count('Overtime Authorization')==before['Overtime Authorization']
  assert frappe.db.count(DT)==before[DT]+1 and frappe.db.count('Additional Salary')==amounts+1
  doc.reload();doc.days[0].status='No Premium';reject(doc.save);doc.reload()
  doc.enabled=0;doc.save();assert auto.process_day(doc.name,'2026-09-14')['status']=='Paused'
  # Pausing or cancelling enrollment does not reverse the native settlement.
  doc.cancel();settled.reload();assert settled.docstatus==1
  from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
  slip=make_salary_slip(assignment.salary_structure,employee=employee.name,posting_date='2026-09-15',ignore_permissions=True)
  slip.insert(ignore_permissions=True);slip.flags.ignore_permissions=True;slip.submit();slip.cancel()
  settled.reload();settled.flags.ignore_permissions=True;settled.cancel()
  replacement=schedule(enabled=1);replacement.submit()
  result=auto.process_day(replacement.name,'2026-09-14');assert result['status']=='Needs Review' and 'cancelada' in result['summary'],result
  assert frappe.db.count(DT)==before[DT]+1
  # Existing human drafts are neither submitted nor overwritten by automation.
  frappe.db.savepoint('ordinary_human_draft')
  frappe.db.delete(DT,{'name':settled.name})
  human=frappe.get_doc({'doctype':DT,'employee':employee.name,'work_date':'2026-09-14','settlement_payroll_date':'2026-09-15','review_reference':'DEV human draft'})
  human.insert(ignore_permissions=True);snapshot=human.evidence_snapshot
  result=auto.process_day(replacement.name,'2026-09-14');assert result['status']=='Needs Review'
  human.reload();assert human.docstatus==0 and human.evidence_snapshot==snapshot
  frappe.db.rollback(save_point='ordinary_human_draft')
  # Current native role/employee permissions are checked as the actual approver,
  # even when the scheduler itself runs as Administrator.
  original_employee=employee
  employee=frappe.copy_doc(employee);employee.name=prefix+'-ROLE';employee.docstatus=0;employee.db_insert()
  assignment=frappe.copy_doc(assignment);assignment.name=prefix+'-ROLE-SSA';assignment.employee=employee.name;assignment.docstatus=1;assignment.db_insert()
  punch('2026-09-14 18:00:00','IN');punch('2026-09-15 02:00:00','OUT')
  username=prefix.lower()+'@example.invalid'
  user=frappe.get_doc({'doctype':'User','name':username,'email':username,'first_name':'DEV Night Approver','enabled':1,'user_type':'System User','send_welcome_email':0});user.db_insert()
  role=frappe.get_doc({'doctype':'Has Role','parent':username,'parenttype':'User','parentfield':'roles','role':'HR Manager'});role.db_insert()
  permission=frappe.get_doc({'doctype':'User Permission','user':username,'allow':'Employee','for_value':employee.name,'apply_to_all_doctypes':1});permission.db_insert()
  frappe.clear_cache(user=username);frappe.set_user(username)
  reject(lambda:schedule(enabled=1))
  frappe.set_user('Administrator')
  current_roles=frappe.db.get_single_value('DGII Payroll Settings','overtime_manual_verification_roles') or ''
  frappe.db.set_single_value('DGII Payroll Settings','overtime_manual_verification_roles',current_roles+'\nHR Manager')
  frappe.set_user(username)
  role_doc=schedule(enabled=1);role_doc.submit();frappe.set_user('Administrator')
  user.db_set('enabled',0)
  result=auto.process_day(role_doc.name,'2026-09-14');assert result['status']=='Needs Review',result
  user.db_set('enabled',1)
  permission.db_set('for_value',original_employee.name);frappe.clear_cache(user=username)
  result=auto.process_day(role_doc.name,'2026-09-14');assert result['status']=='Needs Review',result
  permission.db_set('for_value',employee.name);frappe.clear_cache(user=username)
  result=auto.process_day(role_doc.name,'2026-09-14');assert result['status']=='Created',result
  assert frappe.session.user=='Administrator'
  assert frappe.db.get_value(DT,result['settlement'],'approved_by')==username
  # An actual scheduler sweep invokes the same service, with one transaction
  # per candidate. Test intercepts commits so all fixtures can roll back.
  commits=[]
  frappe.db.set_value(auto.DAY,replacement.days[0].name,'checked_on','2026-01-01 00:00:00')
  with patch.object(frappe.db,'commit',side_effect=lambda:commits.append(True)):auto.scheduled_check()
  assert commits and len(commits)<=30
 print('STANDALONE_NIGHT: explicit bounded enrollment, disabled/paused no-op, missing->arriving exit, atomic post-payment failure rollback, unique5h/75 without OT, immutable daily outcomes, native payroll/cancel, no recreation of cancelled/human draft passed')
finally:
 frappe.set_user('Administrator');frappe.db.rollback();frappe.db.commit=commit;frappe.enqueue=enqueue;frappe.sendmail=sendmail
 after={dt:frappe.db.count(dt) for dt in counts};assert before==after,(before,after)
 for dt,values in settings_before.items():assert values==frappe.db.get_singles_dict(dt),dt
 print('STANDALONE_NIGHT_ROLLBACK',json.dumps(after));frappe.destroy()
