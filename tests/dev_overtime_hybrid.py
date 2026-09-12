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
 'Leave Period','Leave Allocation','Leave Application','Leave Ledger Entry','Overtime Compensatory Credit','Overtime Rest Watch','Working Time Evidence Reference','Overtime Authorization','Overtime Settlement Election','Overtime Reconciliation Run','Ordinary Night Settlement','Additional Salary','Salary Slip','Holiday List','Version','Comment','Error Log']
before={d:frappe.db.count(d) for d in counts}
settings_before={d:frappe.db.get_singles_dict(d) for d in ['DGII Payroll Settings','Payroll Settings','HR Settings']}
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
   'planned_settlement':'Compensatory Rest','settlement_payroll_date':'2026-09-15','reconciliation_engine':retro.ENGINE})
  doc.insert(ignore_permissions=True);doc.flags.ignore_permissions=True;return doc
 from powerpro.controllers import overtime_holiday_base as coverage,overtime_rest as rest
 from powerpro.controllers.overtime_policy_settings import load_version
 from powerpro.controllers.overtime_hybrid_settlement import preview_hybrid
 from powerpro.controllers import overtime_cash_settlement as cash
 from powerpro.controllers import overtime_settlement as settlement
 from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
 leave_type=frappe.db.get_single_value('DGII Payroll Settings','overtime_compensatory_leave_type')
 frappe.db.set_single_value('HR Settings','send_leave_notification',0)
 frappe.db.set_single_value('DGII Payroll Settings','enable_overtime_compensatory_settlement',1)
 period=frappe.get_doc({'doctype':'Leave Period','name':prefix+'-PERIOD','company':employee.company,'from_date':'2026-01-01','to_date':'2026-12-31','is_active':1})
 period.insert(ignore_permissions=True)
 settings=frappe.get_single('DGII Payroll Settings');settings.update(load_version(policy.name))
 settings.update(dict(manage_overtime_pay_policy=1,overtime_policy_compensatory=1,overtime_policy_leave_type=leave_type,
  overtime_policy_hours_per_day=8,overtime_policy_leave_increment=.5,overtime_policy_rest_factor=1,
  overtime_policy_rest_duration=36,overtime_policy_rest_credit=8,overtime_policy_combined_rest=1))
 settings.save()
 for clock,kind in [('21:00:00','IN'),('22:00:00','OUT')]:punch('2026-09-07',clock,kind)
 checks=[]
 for kind in ['retro','auth','auto']:
  frappe.db.savepoint('hybrid_case')
  if kind=='retro':
   source=draft('2026-09-07','21:00:00','22:00:00',1)
  else:
   source=frappe.copy_doc(base);source.name=prefix+'-AUTH';source.employee=employee.name;source.docstatus=1;source.status='Approved'
   source.overtime_work_call=None;source.shift_type=shift.name;source.holiday_list=holiday.name;source.work_date='2026-09-07'
   source.authorization_start='2026-09-07 21:00:00';source.authorization_end='2026-09-07 22:00:00';source.maximum_hours=1
   source.day_classification='Legal Holiday on Weekly Rest';source.evidence_enrolled=1;source.evidence_auto_settle=0
   source.evidence_snapshot=None;source.evidence_last_hash=None;source.evidence_status='Pending';source.evidence_settlement_ready=0
   source.reconciled_on=None;source.reconciliation_source=None;source.settlement_status='Pending';source.settlement_references=None
   source.settlement_breakdown=None;source.settlement_amount=0;source.holiday_cash_status=None;source.compensatory_credit=None
   source.planned_settlement='Compensatory Rest';source.auto_enrolled=0;source.db_insert()
  q=coverage.preview(source.doctype,source.name,1,'DEV salary base coverage')
  assert q['estimate']['total_amount']==115,q
  coverage.apply(source.doctype,source.name,1,'DEV salary base coverage',q['token'])
  if kind=='retro':source.submit()
  else:evidence.process_authorization(source.name)
  source.reload()
  values={'doctype':'Overtime Settlement Election','choice':'Compensatory Rest',
   'employee_reference':'DEV employee chooses rest plus holiday cash','planned_start':'2026-09-15 18:00:00',
   'planned_end':'2026-09-17 06:00:00','settlement_payroll_date':'2026-09-15',
   'retroactive_adjustment' if kind=='retro' else 'authorization':source.name}
  invalid=frappe.get_doc(dict(values,settlement_payroll_date=None))
  try:invalid.insert(ignore_permissions=True)
  except frappe.ValidationError:pass
  else:raise AssertionError('Hybrid election accepted without cash payroll date')
  election=frappe.get_doc(values);election.insert(ignore_permissions=True);rest.approve_election(election.name);source.reload()
  if kind!='retro':evidence.process_authorization(source.name);source.reload()
  if kind=='retro':
   status=retro.get_status(source.name)
   assert status['can_credit'] and status['holiday_cash']['total_amount']==115
  else:assert settlement._build_preview(source,settings=evidence._settings())['holiday_cash']['total_amount']==115
  def create():
   if kind=='retro':return retro.create_compensatory_settlement(source.name)
   if kind=='auto':
    source.db_set('evidence_auto_settle',1)
    result=evidence.process_authorization(source.name)
    if result!='Frozen':raise RuntimeError('Automatic hybrid did not settle: '+str(result))
    return result
   return settlement._settle_authorization(source,settings=evidence._settings())
  # Force failure after money creation: neither output may survive.
  old_counts={dt:frappe.db.count(dt) for dt in ['Additional Salary','Overtime Compensatory Credit']}
  with patch.object(settlement,'create_compensatory_credit',side_effect=RuntimeError('DEV fail after cash')):
   try:create()
   except RuntimeError:pass
   else:raise AssertionError('Injected failure did not execute')
  assert old_counts=={dt:frappe.db.count(dt) for dt in old_counts}
  source.reload();assert source.settlement_status=='Pending' and not source.holiday_cash_status
  result=create();source.reload();election.reload()
  assert source.settlement_status=='Credited' and source.holiday_cash_status=='Created'
  assert source.settlement_amount==115 and source.compensatory_hours==8 and source.compensatory_days==1
  assert election.status=='Credited' and election.minimum_rest_hours==36
  refs=cash._get_linked_additional_salaries(source,docstatus=1)
  assert len(refs)==2 and sum(frappe.db.get_value('Additional Salary',n,'amount') for n in refs)==115
  credited=source.compensatory_credit
  if kind=='auto':assert create()=='Frozen'
  else:
   try:create()
   except frappe.ValidationError:pass
   else:raise AssertionError('Hybrid duplicate created')
  assert cash._get_linked_additional_salaries(source,docstatus=1)==refs
  slip=make_salary_slip(assignment.salary_structure,employee=employee.name,posting_date='2026-09-15',ignore_permissions=True)
  slip.insert(ignore_permissions=True);slip.flags.ignore_permissions=True;slip.submit();source.reload();election.reload()
  assert source.settlement_status=='Credited' and source.holiday_cash_status=='Payroll Submitted'
  assert source.compensatory_credit==credited and election.status=='Credited'
  assert sum(float(r.amount) for r in slip.earnings if r.get('additional_salary') in refs)==115
  try:cash.before_cancel_adjustment(source)
  except frappe.ValidationError:pass
  else:raise AssertionError('Payroll submission did not block reversal')
  slip.cancel();source.reload()
  assert source.holiday_cash_status=='Created' and source.settlement_status=='Credited'
  # Rest scheduling is still available after payroll inclusion and cancellation.
  application=frappe.get_doc({'doctype':'Leave Application','employee':employee.name,'company':employee.company,'leave_type':leave_type,
   'from_date':'2026-09-16','to_date':'2026-09-16','half_day':0,'leave_approver':'Administrator','status':'Approved','posting_date':'2026-09-12','description':'DEV hybrid rest'})
  application.insert(ignore_permissions=True);application.flags.ignore_permissions=True;application.submit()
  rest.link_leave(election.name,application.name);assert election.reload().status=='Scheduled'
  frappe.db.savepoint('consumed_rest_cancel')
  try:
   source.flags.ignore_permissions=True;source.cancel()
  except frappe.ValidationError:frappe.db.rollback(save_point='consumed_rest_cancel')
  else:raise AssertionError('Consumed rest did not prevent cancellation')
  source.reload();application.reload();assert application.docstatus==1 and all(frappe.db.get_value('Additional Salary',n,'docstatus')==1 for n in refs)
  application.flags.ignore_permissions=True;application.cancel();source.reload()
  frappe.db.savepoint('hybrid_review_reversal')
  from powerpro.controllers.automatic_overtime import _reverse_outputs
  _reverse_outputs(source,frappe._dict(name='DEV-revision',reason='DEV corrected evidence'))
  assert frappe.db.get_value('Overtime Compensatory Credit',credited,'docstatus')==2
  assert all(frappe.db.get_value('Additional Salary',n,'docstatus')==2 for n in refs)
  frappe.db.rollback(save_point='hybrid_review_reversal');source.reload()
  source.flags.ignore_permissions=True;source.cancel();source.reload()
  assert source.holiday_cash_status=='Cancelled' and source.settlement_status=='Cancelled'
  assert frappe.db.get_value('Overtime Compensatory Credit',credited,'docstatus')==2
  assert all(frappe.db.get_value('Additional Salary',n,'docstatus')==2 for n in refs)
  assert election.reload().docstatus==2
  checks.append(kind+': atomic cash+rest, failure rollback, payroll independent, scheduling, cancellation, retry')
  frappe.db.rollback(save_point='hybrid_case')
 print(json.dumps({'ok':True,'checks':checks}))
finally:
 frappe.set_user('Administrator');frappe.db.rollback();frappe.db.commit=commit;frappe.enqueue=enqueue;frappe.sendmail=sendmail
 after={d:frappe.db.count(d) for d in counts};assert before==after,(before,after)
 assert settings_before=={d:frappe.db.get_singles_dict(d) for d in settings_before}
 print(json.dumps({'rollback_verified':True,'counts':after}));frappe.destroy()
