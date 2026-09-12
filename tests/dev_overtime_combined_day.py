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
 'Overtime Authorization','Overtime Settlement Election','Overtime Reconciliation Run','Ordinary Night Settlement','Additional Salary','Salary Slip','Holiday List','Version','Comment','Error Log']
before={d:frappe.db.count(d) for d in counts}
settings_before={d:frappe.db.get_singles_dict(d) for d in ['DGII Payroll Settings','Payroll Settings']}
commit,enqueue,sendmail=frappe.db.commit,frappe.enqueue,frappe.sendmail

def forbidden(*args,**kwargs):raise AssertionError('Commit or outbound effect forbidden')
frappe.db.commit=forbidden;frappe.enqueue=forbidden;frappe.sendmail=forbidden
prefix='RETRO-EVIDENCE-DEV-'+uuid.uuid4().hex[:8]
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
 shift.working_hours_calculation_based_on='Every Valid Check-in and Check-out';shift.last_sync_of_checkin='2026-09-30 23:00:00'
 holiday=frappe.get_doc({'doctype':'Holiday List','holiday_list_name':prefix+'-HOL','from_date':'2026-09-01','to_date':'2026-09-30','holidays':[{'holiday_date':'2026-09-07','description':'DEV holiday on weekly rest','weekly_off':1,'custom_is_legal_holiday':1}]})
 holiday.insert(ignore_permissions=True);shift.holiday_list=holiday.name;shift.db_insert()
 employee=frappe.copy_doc(frappe.get_doc('Employee',base.employee));employee.name=prefix+'-EMP';employee.docstatus=0
 employee.employee_name='DEV Retroactive Evidence';employee.user_id=None;employee.company_email=None;employee.personal_email=None
 employee.holiday_list=holiday.name;employee.default_shift=shift.name;employee.overtime_approver='Administrator';employee.status='Active';employee.db_insert()
 name=frappe.get_all('Salary Structure Assignment',filters={'employee':base.employee,'docstatus':1},pluck='name',order_by='from_date desc',limit=1)[0]
 assignment=frappe.copy_doc(frappe.get_doc('Salary Structure Assignment',name));assignment.name=prefix+'-SSA';assignment.employee=employee.name
 assignment.docstatus=1;assignment.from_date='2026-01-01';assignment.base=19064;assignment.salary_per_hour=100;assignment.db_insert()
 policy=frappe.get_doc({'doctype':'Overtime Pay Policy','title':prefix,'company':employee.company,
  'valid_from':'2026-09-01','valid_until':'2026-09-30','approval_reference':'Synthetic40% DEV policy, not actual approval',
  'weekly_threshold':68,'regular_percent':35,'extraordinary_percent':100,'night_percent':15,'weekly_rest_percent':100,
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
 from powerpro.controllers import overtime_holiday_base as coverage, overtime_rest as rest
 from powerpro.controllers.overtime_policy_settings import load_version
 from powerpro.controllers.overtime_cash_settlement import create_cash_settlement
 from powerpro.controllers.overtime_settlement import _settle_authorization
 from powerpro.payroll_rules.overtime_combined_day import REVIEW,SINGLE,ADDITIVE
 for clock,kind in [('21:00:00','IN'),('22:00:00','OUT')]:punch('2026-09-07',clock,kind)
 checks=[]
 for mode,covered,expected in [(REVIEW,0,None),(SINGLE,0,215),(SINGLE,1,115),(ADDITIVE,0,315),(ADDITIVE,1,215)]:
  frappe.db.savepoint('combined_case')
  settings=frappe.get_single('DGII Payroll Settings');settings.update(load_version(policy.name))
  settings.manage_overtime_pay_policy=1;settings.overtime_policy_combined_day=mode
  settings.overtime_policy_weekly_rest_cash=1;settings.save()
  source=draft('2026-09-07','21:00:00','22:00:00',1)
  raw=evidence.build_result(source)
  assert raw['calculation'].get('holiday_weekly_rest_hours')==1, (raw['calculation'], raw['input']['contexts'])
  assert raw['calculation']['holiday_100_hours']==1 and raw['calculation']['weekly_rest_hours']==0
  assert not raw['settlement_ready']
  preview=coverage.preview(DT,source.name,covered,'DEV joint-day salary coverage')
  if expected is None:
   assert preview['estimate'] is None
   assert any('cómo liquidar' in b for b in raw['settlement_blockers'])
   frappe.db.rollback(save_point='combined_case');checks.append('review remains pending');continue
  assert preview['estimate']['total_amount']==expected,preview
  coverage.apply(DT,source.name,covered,'DEV joint-day salary coverage',preview['token'])
  source.submit();source.reload()
  assert source.settlement_status=='Pending' and source.settlement_amount==0
  money_before=frappe.db.count('Additional Salary')
  try:create_cash_settlement(source.name)
  except frappe.ValidationError:pass
  else:raise AssertionError('Joint-day cash bypassed employee election')
  assert frappe.db.count('Additional Salary')==money_before
  election=frappe.get_doc({'doctype':'Overtime Settlement Election','retroactive_adjustment':source.name,
   'choice':'Cash','employee_reference':'DEV explicit employee election','settlement_payroll_date':'2026-09-15'})
  election.insert(ignore_permissions=True);rest.approve_election(election.name);source.reload()
  assert election.reload().weekly_rest==1
  assert retro.reconcile(source)['settlement_ready']
  create_cash_settlement(source.name);source.reload()
  assert source.settlement_amount==expected,source.settlement_breakdown
  assert sum(frappe.db.get_value('Additional Salary',n,'amount') for n in frappe.parse_json(source.settlement_references))==expected
  from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
  slip=make_salary_slip(assignment.salary_structure,employee=employee.name,posting_date='2026-09-15',ignore_permissions=True)
  slip.insert(ignore_permissions=True);slip.flags.ignore_permissions=True;slip.submit()
  refs=set(frappe.parse_json(source.settlement_references))
  assert sum(float(r.amount) for r in slip.earnings if r.get('additional_salary') in refs)==expected
  slip.cancel();source.reload();source.flags.ignore_permissions=True;source.cancel()
  assert all(frappe.db.get_value('Additional Salary',n,'docstatus')==2 for n in refs)
  # A separately reconciled authorization must carry the same joint-hours detail into settlement.
  auth=frappe.copy_doc(base);auth.name=prefix+'-AUTH';auth.employee=employee.name;auth.docstatus=1;auth.status='Approved'
  auth.overtime_work_call=None;auth.shift_type=shift.name;auth.holiday_list=holiday.name;auth.work_date='2026-09-07'
  auth.authorization_start='2026-09-07 21:00:00';auth.authorization_end='2026-09-07 22:00:00';auth.maximum_hours=1
  auth.day_classification='Legal Holiday on Weekly Rest'
  auth.evidence_enrolled=1;auth.evidence_auto_settle=0;auth.evidence_snapshot=None;auth.evidence_last_hash=None
  auth.evidence_status='Pending';auth.evidence_settlement_ready=0;auth.reconciled_on=None;auth.reconciliation_source=None
  auth.settlement_status='Pending';auth.settlement_references=None;auth.settlement_breakdown=None;auth.settlement_amount=0
  auth.planned_settlement='Cash';auth.auto_enrolled=0;auth.db_insert()
  q=coverage.preview(auth.doctype,auth.name,covered,'DEV coverage for AUTH')
  assert q['estimate']['total_amount']==expected
  coverage.apply(auth.doctype,auth.name,covered,'DEV coverage for AUTH',q['token'])
  evidence.process_authorization(auth.name);auth.reload()
  election=frappe.get_doc({'doctype':'Overtime Settlement Election','authorization':auth.name,
   'choice':'Cash','employee_reference':'DEV employee election'})
  election.insert(ignore_permissions=True);rest.approve_election(election.name)
  evidence.process_authorization(auth.name);auth.reload()
  _settle_authorization(auth,payroll_date='2026-09-15',settings=evidence._settings());auth.reload()
  assert auth.settlement_amount==expected,auth.settlement_breakdown
  money_count=frappe.db.count('Additional Salary')
  assert evidence.process_authorization(auth.name)=='Frozen'
  assert frappe.db.count('Additional Salary')==money_count
  checks.append([mode,covered,expected,'native Retro + AUTH + SalarySlip + cancellation + retry'])
  frappe.db.rollback(save_point='combined_case')
 print(json.dumps({'ok':True,'checks':checks}))
finally:
 frappe.set_user('Administrator');frappe.db.rollback();frappe.db.commit=commit;frappe.enqueue=enqueue;frappe.sendmail=sendmail
 after={d:frappe.db.count(d) for d in counts}
 assert before==after,(before,after)
 assert settings_before=={d:frappe.db.get_singles_dict(d) for d in settings_before}
 print(json.dumps({'rollback_verified':True,'counts':after}))
 frappe.destroy()
