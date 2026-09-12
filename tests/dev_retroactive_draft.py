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
 'Overtime Authorization','Overtime Reconciliation Run','Ordinary Night Settlement','Additional Salary','Salary Slip']
before={d:frappe.db.count(d) for d in counts}
settings_before={d:frappe.db.get_singles_dict(d) for d in ['DGII Payroll Settings','Payroll Settings']}
commit,enqueue,sendmail=frappe.db.commit,frappe.enqueue,frappe.sendmail

def forbidden(*args,**kwargs):raise AssertionError('Commit or outbound effect forbidden')
frappe.db.commit=forbidden;frappe.enqueue=forbidden;frappe.sendmail=forbidden
prefix='RETRO-DRAFT-DEV-'+uuid.uuid4().hex[:8]
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
 from powerpro.controllers import retroactive_draft_review as review
 def preview(doc,declaration,reason='DEV initial manual evidence'):
  return review.preview_review(doc.name,reason,manual_declaration=declaration)
 def apply(doc,p,declaration,reason='DEV initial manual evidence'):
  return review.apply_review(doc.name,reason,p['token'],manual_declaration=declaration)
 entrance=punch('2026-09-07','08:00:00','IN')
 first=draft('2026-09-07')
 def reject(fn,expected=(frappe.ValidationError,frappe.PermissionError,ValueError)):
  try:fn()
  except expected:return
  raise AssertionError('Expected refusal')
 reject(first.submit);first.reload()
 declaration={'full_session':True,'reference':'DEV supervisor signed attendance',
  'intervals':[{'start':'2026-09-07 08:00:00','end':'2026-09-07 12:00:00'},
   {'start':'2026-09-07 13:00:00','end':'2026-09-07 20:00:00'}]}
 frappe.db.set_single_value('DGII Payroll Settings','enable_manual_overtime_verification',0)
 reject(lambda:preview(first,declaration))
 frappe.db.set_single_value('DGII Payroll Settings','enable_manual_overtime_verification',1)
 reject(lambda:preview(first,{**declaration,'full_session':False}))
 reject(lambda:preview(first,{**declaration,'reference':''}))
 p=preview(first,declaration);assert p['draft_only'] and p['after']['verified_hours']==2
 money=frappe.db.count('Additional Salary');punches=frappe.db.count('Employee Checkin')
 entrance.time='2026-09-07 08:01:00';entrance.save(ignore_permissions=True)
 reject(lambda:apply(first,p,declaration))
 p=preview(first,declaration)
 first.db_set('approver','Guest');reject(lambda:apply(first,p,declaration));first.db_set('approver','Administrator')
 p=preview(first,declaration);accepted=apply(first,p,declaration)
 assert apply(first,p,declaration)['idempotent']
 first.reload();assert first.docstatus==0 and not first.evidence_snapshot
 assert frappe.db.count('Additional Salary')==money and frappe.db.count('Employee Checkin')==punches
 audit=frappe.get_doc('Overtime Reconciliation Run',accepted['audit'])
 assert frappe.parse_json(audit.evidence)['after']['review']['reviewed_by']=='Administrator'
 assert frappe.parse_json(audit.evidence)['after']['review']['initial_draft']
 audit.issues='tampered';reject(audit.save)
 p=retro.reconcile(first);assert p['verified_hours']==2 and p['evidence_state']=='Verified'
 entrance.time='2026-09-07 08:02:00';entrance.save(ignore_permissions=True)
 assert retro.reconcile(first)['evidence_state']=='Needs Review'
 reject(first.submit);first.reload()
 p=preview(first,declaration);apply(first,p,declaration)
 frappe.db.set_single_value('DGII Payroll Settings','enable_manual_overtime_verification',0)
 reject(first.submit);first.reload()
 frappe.db.set_single_value('DGII Payroll Settings','enable_manual_overtime_verification',1)
 first.db_set('approver','Guest');assert retro.reconcile(first)['evidence_state']=='Needs Review'
 first.db_set('approver','Administrator')
 first.submit();first.reload()
 assert first.reconciliation_source=='Manual Verification' and first.verified_hours==2 and first.settlement_amount==280
 assert frappe.db.count('Employee Checkin')==punches
 frozen=frappe.parse_json(first.evidence_snapshot)
 assert frozen['review']['initial_draft'] and frozen['review']['manual_declaration']['reference']==declaration['reference']
 assert frozen['checkin_comparison']['state']!='Verified'
 # The resulting manual proof must pass the same native payroll check as other evidence.
 from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
 slip=make_salary_slip(assignment.salary_structure,employee=employee.name,posting_date='2026-09-15',ignore_permissions=True)
 slip.insert(ignore_permissions=True);slip.flags.ignore_permissions=True;slip.submit();slip.cancel()
 first.reload();first.flags.ignore_permissions=True;first.cancel()
 # A complete documentary declaration may support a day with no punches at all.
 employee=frappe.copy_doc(employee);employee.name=prefix+'-NO-PUNCH';employee.docstatus=0;employee.db_insert()
 assignment=frappe.copy_doc(assignment);assignment.name=prefix+'-NO-PUNCH-SSA';assignment.employee=employee.name;assignment.docstatus=1;assignment.db_insert()
 empty=draft('2026-09-07');reject(empty.submit);empty.reload()
 p=preview(empty,declaration);apply(empty,p,declaration)
 empty.submit();empty.reload()
 assert empty.verified_hours==2 and empty.settlement_amount==280 and empty.reconciliation_source=='Manual Verification'
 assert frappe.parse_json(empty.source_checkins)==[] and frappe.db.count('Employee Checkin')==punches
 empty.flags.ignore_permissions=True;empty.cancel()
 print('RETRO_DRAFT: missing exit -> reviewed full-session audit -> explicit native approval/cash280/payroll; stale inputs/approver/disabled manual rejected; draft preserved, immutable audit, idempotent, no fabricated punches passed')
finally:
 frappe.db.rollback();frappe.db.commit=commit;frappe.enqueue=enqueue;frappe.sendmail=sendmail
 after={d:frappe.db.count(d) for d in counts}
 assert before==after,(before,after)
 for dt,values in settings_before.items():assert values==frappe.db.get_singles_dict(dt),dt
 print('RETRO_DRAFT_ROLLBACK',json.dumps(after))
 frappe.destroy()
