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
 'Overtime Work Call','Overtime Authorization','Overtime Reconciliation Run','Ordinary Night Settlement','Additional Salary','Salary Slip']
before={d:frappe.db.count(d) for d in counts}
settings_before={d:frappe.db.get_singles_dict(d) for d in ['DGII Payroll Settings','Payroll Settings']}
commit,enqueue,sendmail=frappe.db.commit,frappe.enqueue,frappe.sendmail

def forbidden(*args,**kwargs):raise AssertionError('Commit or outbound effect forbidden')
frappe.db.commit=forbidden;frappe.enqueue=forbidden;frappe.sendmail=forbidden
prefix='WORK-CONTROLS-DEV-'+uuid.uuid4().hex[:8]
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
 for day in ['2026-09-07','2026-09-09']:
  for clock,kind in [('08:00:00','IN'),('12:00:00','OUT'),('13:00:00','IN'),('20:00:00','OUT')]:punch(day,clock,kind)
 first=draft('2026-09-07');first.submit();first.reload()
 second=draft('2026-09-09');second.submit();second.reload()
 snapshots={doc.name:doc.as_dict() for doc in [first,second]}
 actual_sql=frappe.db.sql
 def readonly(query,*args,**kwargs):
  if str(query).lstrip().split(' ',1)[0].lower() in {'insert','update','delete','replace','alter','drop','truncate'}:
   raise AssertionError('Diagnostic attempted a database write')
  return actual_sql(query,*args,**kwargs)
 def check(r,code):return next(c for c in r['controls'] if c['code']==code)
 with patch.object(frappe.db,'sql',side_effect=readonly):
  r=controls.preview(DT,first.name)
  assert check(r,'daily_work')['observed']==11 and check(r,'daily_work')['status']=='Review'
  assert check(r,'work_break')['status']=='Review'
  assert check(r,'quarterly_extension')['observed']==4 and check(r,'quarterly_extension')['status']=='Applicability review',r
  assert not r['affects_payment'] and not r['compliance_certified']
  assert r['input_hash']==controls.preview(DT,first.name)['input_hash']
  r=controls.preview(DT,second.name,quarterly_basis='Extraordinary workload')
  assert check(r,'weekly_work')['status']=='Incomplete',r
  assert check(r,'quarterly_extension')['status']=='Incomplete'
  r=controls.preview(DT,first.name,rest_start='2026-09-07 00:00:00',rest_end='2026-09-08 12:00:00')
  assert check(r,'weekly_continuous_rest')['recorded_work_hours']==11 and check(r,'weekly_continuous_rest')['status']=='Review'
  r=controls.preview(DT,first.name,profile='Agreed industrial continuous day',reference='DEV example agreement')
  assert check(r,'daily_work')['limit']==9 and check(r,'work_break')['status']=='Documented regime required'
 for doc in [first,second]:doc.reload();assert doc.as_dict()==snapshots[doc.name]
 original_permissions=frappe.has_permission
 def no_checkins(dt,*args,**kwargs):return False if dt=='Employee Checkin' else original_permissions(dt,*args,**kwargs)
 with patch.object(frappe,'has_permission',side_effect=no_checkins):
  try:controls.preview(DT,first.name)
  except frappe.PermissionError:pass
  else:raise AssertionError('Control preview bypassed Checkin permission')
 # A changed old source is explicitly excluded from the quarter lower bound.
 exit_name=frappe.db.get_value('Employee Checkin',{'employee':employee.name,'time':'2026-09-07 20:00:00'},'name')
 exit_doc=frappe.get_doc('Employee Checkin',exit_name);exit_doc.time='2026-09-07 19:00:00';exit_doc.save(ignore_permissions=True)
 r=controls.preview(DT,second.name)
 assert check(r,'quarterly_extension')['observed']==2 and any(i.get('source_name')==first.name for i in r['evidence_issues'])
 # Ordinary-night sources reuse their complete shift with the same diagnostics.
 from powerpro.controllers import ordinary_night as night
 shift2=frappe.copy_doc(shift);shift2.name=prefix+'-EVENING';shift2.docstatus=0;shift2.start_time='16:00:00';shift2.end_time='22:00:00';shift2.db_insert()
 employee=frappe.copy_doc(employee);employee.name=prefix+'-NIGHT';employee.default_shift=shift2.name;employee.docstatus=0;employee.db_insert()
 assignment=frappe.copy_doc(assignment);assignment.name=prefix+'-NIGHT-SSA';assignment.employee=employee.name;assignment.docstatus=1;assignment.db_insert()
 punch('2026-09-07','16:00:00','IN');punch('2026-09-07','22:00:00','OUT')
 noct=frappe.get_doc({'doctype':night.DT,'employee':employee.name,'work_date':'2026-09-07','settlement_payroll_date':'2026-09-15','review_reference':'DEV controls'})
 noct.insert(ignore_permissions=True);noct.flags.ignore_permissions=True;noct.submit();noct.reload();saved=noct.as_dict()
 with patch.object(frappe.db,'sql',side_effect=readonly):r=controls.preview(night.DT,noct.name)
 assert check(r,'daily_work')['observed']==6 and check(r,'work_break')['status']=='Review'
 noct.reload();assert saved==noct.as_dict()
 # Exercise the native Work Call -> enrolled Authorization route as well.
 punch('2026-09-14','16:00:00','IN');punch('2026-09-14','23:00:00','OUT')
 call=frappe.copy_doc(frappe.get_doc('Overtime Work Call','CONV-HE-2026-00004-1'));call.name=None;call.docstatus=0
 call.company=employee.company;call.from_date='2026-09-14';call.to_date='2026-09-14';call.planned_settlement='Cash'
 call.automation_mode='Verified Checkins';call.evidence_auto_settle=0
 call.set('employees',[]);call.append('employees',{'employee':employee.name})
 call.set('dates',[]);call.append('dates',{'work_date':'2026-09-14','start_time':'22:00:00','end_time':'23:00:00','requested_hours':1})
 call.insert(ignore_permissions=True);call.flags.ignore_permissions=True;call.submit()
 name=frappe.db.get_value('Overtime Authorization',{'overtime_work_call':call.name},'name')
 with patch.object(evidence,'now_datetime',return_value=get_datetime('2026-09-15 10:00:00')):
  assert evidence.process_authorization(name)=='Verified'
  with patch.object(frappe.db,'sql',side_effect=readonly):r=controls.preview('Overtime Authorization',name)
  assert check(r,'daily_work')['observed']==7
  assert check(r,'quarterly_extension')['observed']==1
 print('WORK_CONTROLS: live full-session daily/pause checks, incomplete weekly/quarter coverage, conditional regime and rest overlap, stale quarter exclusion, native read permission and zero SQL writes on retro/night sources passed')
finally:
 frappe.db.rollback();frappe.db.commit=commit;frappe.enqueue=enqueue;frappe.sendmail=sendmail
 after={d:frappe.db.count(d) for d in counts};assert before==after,(before,after)
 for dt,values in settings_before.items():assert values==frappe.db.get_singles_dict(dt),dt
 print('WORK_CONTROLS_ROLLBACK',json.dumps(after));frappe.destroy()
