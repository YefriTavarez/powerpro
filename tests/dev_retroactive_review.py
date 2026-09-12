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
prefix='RETRO-REVIEW-DEV-'+uuid.uuid4().hex[:8]
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
 from powerpro.controllers import checkin_overtime_review as review
 def preview(doc,reason='DEV corrected exit',declaration=None):
  return review.preview_review(doc.name,reason,manual_declaration=declaration,source_type=DT)
 def apply(doc,p,reason='DEV corrected exit',declaration=None):
  return review.apply_review(doc.name,reason,p['token'],manual_declaration=declaration,source_type=DT)
 for clock,kind in [('08:00:00','IN'),('12:00:00','OUT'),('13:00:00','IN')]:punch('2026-09-07',clock,kind)
 last=punch('2026-09-07','20:00:00','OUT')
 first=draft('2026-09-07');first.submit();first.reload()
 assert first.settlement_amount==280
 old_refs=_get_linked_additional_salaries(first,docstatus=1)
 last.time='2026-09-07 19:00:00';last.save(ignore_permissions=True)
 p=preview(first);assert p['proposed_amount']==140 and p['before']['verified_hours']==2 and p['after']['verified_hours']==1
 assert p['retroactive_adjustment']==first.name and 'authorization' not in p
 last.time='2026-09-07 18:30:00';last.save(ignore_permissions=True)
 try:apply(first,p)
 except frappe.ValidationError:pass
 else:raise AssertionError('Stale review token accepted')
 last.time='2026-09-07 19:00:00';last.save(ignore_permissions=True)
 p=preview(first)
 orig=retro.settle_reviewed_cash
 def fail_after_cash(doc,result):
  orig(doc,result)
  raise RuntimeError('DEV injected replacement failure')
 with patch.object(retro,'settle_reviewed_cash',side_effect=fail_after_cash):
  try:apply(first,p)
  except RuntimeError:pass
  else:raise AssertionError('Failure injection did not run')
 first.reload();assert first.settlement_amount==280 and first.verified_hours==2
 assert _get_linked_additional_salaries(first,docstatus=1)==old_refs
 result=apply(first,p);first.reload()
 assert first.settlement_amount==140 and first.verified_hours==1 and first.reconciliation_source=='Employee Checkin'
 assert all(frappe.db.get_value('Additional Salary',name,'docstatus')==2 for name in old_refs)
 assert len(_get_linked_additional_salaries(first,docstatus=1))==1
 assert apply(first,p)['idempotent']
 audit=frappe.get_doc('Overtime Reconciliation Run',result['audit'])
 assert audit.retroactive_adjustment==first.name and not audit.authorization
 assert frappe.parse_json(audit.evidence)['financial_before']['settlement_amount']==280
 # Already settled later overtime must be resolved before changing its real-week basis.
 for clock,kind in [('08:00:00','IN'),('12:00:00','OUT'),('13:00:00','IN'),('20:00:00','OUT')]:punch('2026-09-08',clock,kind)
 second=draft('2026-09-08');second.submit();second.reload()
 last.time='2026-09-07 18:30:00';last.save(ignore_permissions=True)
 p=preview(first)
 assert any(r['name']==second.name and r['blocks_reversal'] for r in p['dependencies'])
 try:apply(first,p)
 except frappe.ValidationError as exc:assert second.name in str(exc)
 else:raise AssertionError('Settled historical dependent was ignored')
 second.flags.ignore_permissions=True;second.cancel()
 p=preview(first);apply(first,p);first.reload();assert first.settlement_amount==70
 from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
 slip=make_salary_slip(assignment.salary_structure,employee=employee.name,posting_date='2026-09-15',ignore_permissions=True)
 slip.insert(ignore_permissions=True);slip.flags.ignore_permissions=True;slip.submit()
 last.time='2026-09-07 19:00:00';last.save(ignore_permissions=True)
 p=preview(first)
 try:apply(first,p)
 except frappe.ValidationError:pass
 else:raise AssertionError('Review replaced earnings already included in submitted payroll')
 slip.cancel();p=preview(first);apply(first,p);first.reload();assert first.settlement_amount==140
 # HR can replace a now-invalid punch with a full-session declaration. Punches
 # remain unchanged and are frozen as comparison, never synthetic attendance.
 last.skip_auto_attendance=1;last.save(ignore_permissions=True)
 declaration={'full_session':True,'reference':'DEV signed complete-session record',
  'intervals':[{'start':'2026-09-07 08:00:00','end':'2026-09-07 12:00:00'},
               {'start':'2026-09-07 13:00:00','end':'2026-09-07 19:30:00'}]}
 punch_count=frappe.db.count('Employee Checkin')
 p=preview(first,'DEV declared actual session',declaration)
 apply(first,p,'DEV declared actual session',declaration);first.reload()
 assert first.verified_hours==1.5 and first.settlement_amount==210 and first.reconciliation_source=='Manual Verification'
 assert frappe.db.count('Employee Checkin')==punch_count
 assert frappe.db.get_value('Employee Checkin',last.name,'skip_auto_attendance')==1
 frozen=frappe.parse_json(first.evidence_snapshot);assert frozen['review']['manual_declaration']['reference']==declaration['reference']
 frappe.db.savepoint('manual_flag_off')
 frappe.db.set_single_value('DGII Payroll Settings','enable_manual_overtime_verification',0)
 try:retro.validate_fresh(first)
 except frappe.ValidationError:pass
 else:raise AssertionError('Manual new-money flag bypassed')
 frappe.db.rollback(save_point='manual_flag_off')
 retro.validate_fresh(first,payroll=True)
 first.flags.ignore_permissions=True;first.cancel()
 assert first.settlement_status=='Cancelled'
 # A declared retroactive full session also supplies ordinary night evidence.
 from powerpro.controllers import ordinary_night as night
 from powerpro.controllers.overtime_cash_settlement import create_cash_settlement
 evening=frappe.copy_doc(shift);evening.name=prefix+'-EVENING';evening.docstatus=0
 evening.start_time='16:00:00';evening.end_time='22:00:00';evening.db_insert()
 employee=frappe.copy_doc(employee);employee.name=prefix+'-NIGHT-EMP';employee.docstatus=0;employee.default_shift=evening.name;employee.db_insert()
 assignment=frappe.copy_doc(assignment);assignment.name=prefix+'-NIGHT-SSA';assignment.docstatus=1;assignment.employee=employee.name;assignment.db_insert()
 punch('2026-09-07','18:00:00','IN');exit_night=punch('2026-09-07','23:00:00','OUT')
 adjustment=draft('2026-09-07','22:00:00','23:00:00',1);adjustment.submit();adjustment.reload()
 exit_night.skip_auto_attendance=1;exit_night.save(ignore_permissions=True)
 declaration={'full_session':True,'reference':'DEV signed night shift record',
  'intervals':[{'start':'2026-09-07 18:00:00','end':'2026-09-07 23:00:00'}]}
 p=preview(adjustment,'DEV declared night session',declaration)
 apply(adjustment,p,'DEV declared night session',declaration);adjustment.reload()
 assert adjustment.reconciliation_source=='Manual Verification' and adjustment.settlement_status=='Pending'
 def create_night():
  doc=frappe.get_doc({'doctype':night.DT,'employee':employee.name,'work_date':'2026-09-07',
    'settlement_payroll_date':'2026-09-15','review_reference':'DEV declared retroactive coverage'})
  doc.insert(ignore_permissions=True);doc.flags.ignore_permissions=True;doc.submit();return doc
 night_doc=create_night()
 assert night_doc.settlement_amount==15
 assert frappe.parse_json(night_doc.evidence_snapshot)['input']['certified_session']['retroactive_adjustment']==adjustment.name
 create_cash_settlement(adjustment.name);adjustment.reload();assert adjustment.settlement_amount==155
 # A corrected real punch supersedes the declaration. Stale night coverage must
 # block financial replacement, without blocking HR's evidence correction.
 exit_night.skip_auto_attendance=0;exit_night.time='2026-09-07 22:30:00';exit_night.save(ignore_permissions=True)
 p=preview(adjustment)
 assert not p['settlement_ready']
 apply(adjustment,p);adjustment.reload()
 assert adjustment.verified_hours==.5 and adjustment.settlement_status=='Pending'
 assert adjustment.reconciliation_source=='Employee Checkin'
 assert not _get_linked_additional_salaries(adjustment,docstatus=1)
 night_doc.cancel();night_doc=create_night();create_cash_settlement(adjustment.name);adjustment.reload()
 assert adjustment.settlement_amount==77.5 and night_doc.settlement_amount==15
 adjustment.flags.ignore_permissions=True;adjustment.cancel();night_doc.cancel()
 print('RETRO_NIGHT_REVIEW: declared session supplies ordinary15 plus retroactive155; corrected punch reverses OT, requires replacement night coverage and settles .5h/77.5 once')
 print('RETRO_REVIEW: source-scoped token/audit, stale token, atomic replacement failure, 280->140, idempotency, dependent/payroll guards and missing-exit HR declaration 1.5h/210 passed')
finally:
 frappe.db.rollback();frappe.db.commit=commit;frappe.enqueue=enqueue;frappe.sendmail=sendmail
 after={d:frappe.db.count(d) for d in counts}
 assert before==after,(before,after)
 for dt,values in settings_before.items():assert values==frappe.db.get_singles_dict(dt),dt
 print('RETRO_REVIEW_ROLLBACK',json.dumps(after))
 frappe.destroy()
