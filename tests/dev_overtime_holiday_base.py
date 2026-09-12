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
 'Overtime Authorization','Overtime Reconciliation Run','Ordinary Night Settlement','Additional Salary','Salary Slip','Holiday List','Version','Comment','Error Log']
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
 holiday=frappe.get_doc({'doctype':'Holiday List','holiday_list_name':prefix+'-HOL','from_date':'2026-09-01','to_date':'2026-09-30','holidays':[{'holiday_date':'2026-09-07','description':'DEV isolated holiday','weekly_off':0}]})
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
 for clock,kind in [('21:00:00','IN'),('22:00:00','OUT')]:punch('2026-09-07',clock,kind)
 source=draft('2026-09-07','21:00:00','22:00:00',1)
 from powerpro.controllers import overtime_holiday_base as coverage
 from powerpro.controllers.overtime_cash_settlement import build_cash_settlement,create_cash_settlement
 frappe.db.set_single_value('DGII Payroll Settings','enable_checkin_overtime_reconciliation',0)
 messages=len(frappe.local.message_log)
 assert coverage.get_status(DT,source.name)=={'can_declare':False}
 assert len(frappe.local.message_log)==messages
 frappe.db.set_single_value('DGII Payroll Settings','enable_checkin_overtime_reconciliation',1)
 raw=evidence.build_result(source)
 assert raw['snapshot']['holiday_100_hours']==1,raw
 assert raw['snapshot']['night_hours']==1,raw
 assert coverage.MISSING in raw['settlement_blockers'] and not raw['settlement_ready']
 before_money=frappe.db.count('Additional Salary')
 for bad in [-1,2,'NaN','Infinity']:
  try:coverage.preview(DT,source.name,bad,'DEV salary reference')
  except (ValueError,frappe.ValidationError):pass
  else:raise AssertionError('Invalid covered hours accepted')
 p=coverage.preview(DT,source.name,1,'DEV salary includes this one holiday hour')
 assert p['estimate']['total_amount']==115,p
 assert p['estimate']['holiday_base_already_in_salary']==100
 assert frappe.db.count('Additional Salary')==before_money
 try:coverage.apply(DT,source.name,0,p['declaration']['reference'],p['token'])
 except frappe.ValidationError:pass
 else:raise AssertionError('Different declaration accepted with old token')
 applied=coverage.apply(DT,source.name,1,p['declaration']['reference'],p['token'])
 assert coverage.apply(DT,source.name,1,p['declaration']['reference'],p['token'])['idempotent']
 current=evidence.build_result(source)
 assert current['settlement_ready'],current['settlement_blockers']
 assert current['calculation']['holiday_base_covered_hours']==1
 assert current['holiday_base_coverage']['declared_by']=='Administrator'
 assert current['holiday_base_coverage']['audit']==applied['audit']
 assert frappe.db.count('Additional Salary')==before_money
 # Salary changes invalidate the coverage and stale preview, without silently reducing pay.
 stale=coverage.preview(DT,source.name,.5,'DEV partial coverage')
 assignment.db_set('salary_per_hour',101)
 assert not evidence.build_result(source)['settlement_ready']
 try:coverage.apply(DT,source.name,.5,'DEV partial coverage',stale['token'])
 except frappe.ValidationError:pass
 else:raise AssertionError('Changed salary accepted with old token')
 assignment.db_set('salary_per_hour',100)
 # Genuine native retroactive submission creates only the unpaid balance.
 source.submit();source.reload()
 assert source.settlement_amount==115,source.settlement_breakdown
 frozen=frappe.parse_json(source.settlement_breakdown)
 assert frozen['holiday_base_coverage']['audit']==applied['audit']
 assert sorted(frappe.db.get_value('Additional Salary',n,'amount') for n in frappe.parse_json(source.settlement_references))==[15,100]
 try:coverage.preview(DT,source.name,0,'Cannot replace a settled declaration')
 except frappe.ValidationError:pass
 else:raise AssertionError('Settled source allowed coverage change')
 # Native Salary Slip includes the linked increments once and validates frozen evidence.
 from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
 slip=make_salary_slip(assignment.salary_structure,employee=employee.name,posting_date='2026-09-15',ignore_permissions=True)
 slip.insert(ignore_permissions=True);slip.flags.ignore_permissions=True;slip.submit()
 refs=set(frappe.parse_json(source.settlement_references))
 assert sum(float(r.amount) for r in slip.earnings if r.get('additional_salary') in refs)==115
 slip.cancel();source.reload();source.flags.ignore_permissions=True;source.cancel()
 # Same real evidence with a separate AUTH source: explicit zero coverage pays full 215.
 # Remove cancelled retroactive document from competing active sources; reuse its employee.
 auth=frappe.copy_doc(base);auth.name=prefix+'-AUTH';auth.employee=employee.name;auth.docstatus=1;auth.status='Approved'
 auth.overtime_work_call=None;auth.shift_type=shift.name;auth.holiday_list=holiday.name;auth.work_date='2026-09-07'
 auth.authorization_start='2026-09-07 21:00:00';auth.authorization_end='2026-09-07 22:00:00';auth.maximum_hours=1
 auth.evidence_enrolled=1;auth.evidence_auto_settle=0;auth.evidence_snapshot=None;auth.evidence_last_hash=None
 auth.evidence_status='Pending';auth.evidence_settlement_ready=0;auth.reconciled_on=None;auth.reconciliation_source=None
 auth.settlement_status='Pending';auth.settlement_references=None;auth.settlement_breakdown=None;auth.settlement_amount=0
 auth.planned_settlement='Cash';auth.auto_enrolled=0;auth.db_insert()
 q=coverage.preview(auth.doctype,auth.name,0,'DEV base not included for these hours')
 assert q['estimate']['total_amount']==215
 coverage.apply(auth.doctype,auth.name,0,q['declaration']['reference'],q['token'])
 assert evidence.process_authorization(auth.name)=='Verified'
 auth.reload()
 from powerpro.controllers.overtime_settlement import _settle_authorization
 _settle_authorization(auth,payroll_date='2026-09-15',settings=evidence._settings());auth.reload()
 assert auth.settlement_amount==215
 # Permission denial and audit immutability are enforced on actual native documents.
 frappe.set_user('Guest')
 try:coverage.preview(DT,source.name,0,'unauthorized')
 except frappe.PermissionError:pass
 else:raise AssertionError('Guest was allowed to declare salary coverage')
 frappe.set_user('Administrator')
 audit=frappe.get_doc('Overtime Reconciliation Run',applied['audit']);audit.evidence='{}'
 try:audit.save(ignore_permissions=True)
 except frappe.ValidationError:pass
 else:raise AssertionError('Coverage audit was editable')
 print(json.dumps({'ok':True,'retroactive_additional':115,'authorization_additional':215,
   'checks':['explicit coverage required','finite bounded hours','stale/tampered tokens refused','idempotent apply',
   'salary change blocks','immutable audit','native Additional Salary and Salary Slip','settled source protected','Guest denied']},ensure_ascii=False))
finally:
 frappe.set_user('Administrator');frappe.db.rollback();frappe.db.commit=commit;frappe.enqueue=enqueue;frappe.sendmail=sendmail
 after={d:frappe.db.count(d) for d in counts}
 assert before==after,(before,after)
 assert settings_before=={d:frappe.db.get_singles_dict(d) for d in settings_before}
 print(json.dumps({'rollback_verified':True,'counts':after}))
 frappe.destroy()
