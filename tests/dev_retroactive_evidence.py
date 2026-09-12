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
 for day in ['2026-09-07','2026-09-08']:
  for clock,kind in [('08:00:00','IN'),('12:00:00','OUT'),('13:00:00','IN')]:punch(day,clock,kind)
 first=draft('2026-09-07')
 before_money=frappe.db.count('Additional Salary')
 preview=get_retroactive_adjustment_preview(first.name)
 assert preview['evidence_state']=='Needs Review' and not preview['settlement_ready']
 try:first.submit()
 except frappe.ValidationError:pass
 else:raise AssertionError('Retroactive submission accepted missing exit')
 first.reload();first.flags.ignore_permissions=True
 last=punch('2026-09-07','20:00:00','OUT')
 preview=get_retroactive_adjustment_preview(first.name)
 assert preview['verified_hours']==2 and preview['cash_settlement']['total_amount']==280,preview
 assert frappe.db.count('Additional Salary')==before_money
 projection=frappe._dict(first.as_dict());projection.doctype='Overtime Authorization';projection.name=prefix+'-PROJECTION'
 projected=evidence.build_result(projection)
 assert evidence._evidence_hash(projected['snapshot'])==evidence._evidence_hash(preview['_evidence']['snapshot'])
 assert evidence._evidence_hash(projected['weekly_evidence'])==evidence._evidence_hash(preview['_evidence']['weekly_evidence'])
 first.submit();first.reload()
 assert first.verified_hours==2 and first.settlement_amount==280 and first.reconciliation_source=='Employee Checkin'
 assert first.actual_start==get_datetime('2026-09-07 18:00:00') and first.actual_end==get_datetime('2026-09-07 20:00:00')
 frozen=get_retroactive_adjustment_preview(first.name)
 assert frozen['snapshot'] and frozen['rates']['regular_overtime_percent']==40
 punch('2026-09-08','20:00:00','OUT')
 second=draft('2026-09-08');second.submit();second.reload()
 weekly=frappe.parse_json(second.evidence_snapshot)['calculation']['segments'][0]['actual_weekly_hours_before']
 assert weekly==20,weekly
 assert second.settlement_amount==280
 # Cancelling money does not erase already verified physical work from Tuesday.
 first.cancel()
 current=retro.validate_fresh(second,payroll=True)
 assert current['verified_hours']==2 and current['_evidence']['calculation']['segments'][0]['actual_weekly_hours_before']==20
 from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
 slip=make_salary_slip(assignment.salary_structure,employee=employee.name,posting_date='2026-09-15',ignore_permissions=True)
 slip.insert(ignore_permissions=True);slip.flags.ignore_permissions=True
 frappe.db.savepoint('changed_historical_work')
 last.time='2026-09-07 19:00:00';last.save(ignore_permissions=True)
 try:slip.submit()
 except frappe.ValidationError as exc:assert first.name in str(exc),str(exc)
 else:raise AssertionError('Payroll accepted changed earlier historical work')
 second.reload();assert second.settlement_amount==280 and second.verified_hours==2
 frappe.db.rollback(save_point='changed_historical_work');slip.reload();slip.flags.ignore_permissions=True
 slip.submit();second.reload();assert second.settlement_status=='Payroll Submitted'
 try:second.cancel()
 except frappe.ValidationError:pass
 else:raise AssertionError('Retroactive cancellation bypassed native submitted payroll')
 slip.cancel();second.reload();second.flags.ignore_permissions=True;second.cancel()
 assert not _get_linked_additional_salaries(second,docstatus=1)
 # A separate employee avoids changing the earlier employees' historical shift.
 from powerpro.controllers import ordinary_night as night
 from powerpro.controllers.overtime_cash_settlement import create_cash_settlement
 evening_shift=frappe.copy_doc(shift);evening_shift.name=prefix+'-EVENING';evening_shift.docstatus=0;evening_shift.start_time='16:00:00';evening_shift.end_time='22:00:00';evening_shift.db_insert()
 employee=frappe.copy_doc(employee);employee.name=prefix+'-NIGHT-EMP';employee.docstatus=0;employee.default_shift=evening_shift.name;employee.db_insert()
 assignment=frappe.copy_doc(assignment);assignment.name=prefix+'-NIGHT-SSA';assignment.docstatus=1;assignment.employee=employee.name;assignment.db_insert()
 punch('2026-09-07','18:00:00','IN');night_exit=punch('2026-09-07','23:00:00','OUT')
 adjustment=draft('2026-09-07','22:00:00','23:00:00',1);adjustment.submit();adjustment.reload()
 assert adjustment.verified_hours==1 and adjustment.settlement_status=='Pending' and not adjustment.evidence_settlement_ready
 status=retro.get_status(adjustment.name)
 assert status['can_night'] and status['ordinary_night_hours']==1 and not status['settlement_ready']
 night_doc=frappe.get_doc({'doctype':night.DT,'employee':employee.name,'work_date':'2026-09-07',
  'settlement_payroll_date':'2026-09-15','review_reference':'DEV coverage for '+adjustment.name})
 night_doc.insert(ignore_permissions=True);night_doc.flags.ignore_permissions=True;night_doc.submit()
 assert night_doc.settlement_amount==15 and night_doc.night_hours==1
 assert frappe.parse_json(night_doc.evidence_snapshot)['input']['extensions'][0]['source_type']==DT
 status=retro.get_status(adjustment.name)
 assert status['settlement_ready'] and status['ordinary_night']==night_doc.name
 amount=create_cash_settlement(adjustment.name)
 adjustment.reload();assert amount['total_amount']==155 and adjustment.settlement_amount==155
 assert frappe.parse_json(adjustment.evidence_snapshot)['ordinary_night_settlement']['name']==night_doc.name
 try:night_doc.cancel()
 except frappe.ValidationError as exc:assert adjustment.name in str(exc),str(exc)
 else:raise AssertionError('Night coverage cancelled before settled retroactive source')
 night_doc.reload();night_doc.flags.ignore_permissions=True
 money_count=frappe.db.count('Additional Salary')
 try:create_cash_settlement(adjustment.name)
 except frappe.ValidationError:pass
 else:raise AssertionError('Duplicate retroactive cash accepted')
 assert frappe.db.count('Additional Salary')==money_count
 combined=make_salary_slip(assignment.salary_structure,employee=employee.name,posting_date='2026-09-15',ignore_permissions=True)
 combined.insert(ignore_permissions=True);combined.flags.ignore_permissions=True
 frappe.db.savepoint('retroactive_night_source_changed')
 night_exit.time='2026-09-07 22:30:00';night_exit.save(ignore_permissions=True)
 assert retro.get_status(adjustment.name)['state']=='Needs Review'
 try:combined.submit()
 except frappe.ValidationError:pass
 else:raise AssertionError('Combined payroll accepted changed night/retroactive evidence')
 frappe.db.rollback(save_point='retroactive_night_source_changed');combined.reload();combined.flags.ignore_permissions=True
 combined.submit();adjustment.reload();night_doc.reload()
 assert adjustment.settlement_status==night_doc.settlement_status=='Payroll Submitted'
 combined.cancel();adjustment.reload();adjustment.flags.ignore_permissions=True;adjustment.cancel()
 night_doc.reload();night_doc.flags.ignore_permissions=True;night_doc.cancel()
 assert not _get_linked_additional_salaries(adjustment,docstatus=1) and not _get_linked_additional_salaries(night_doc,docstatus=1)
 print('RETROACTIVE_NIGHT_ACCEPTANCE: approved pending OT resolves ordinary15 plus retroactive155, explicit unique cash settlement, linked cancellation guard, live stale status and native combined payroll/cancel')
 print('RETROACTIVE_EVIDENCE_ACCEPTANCE: missing exit blocks, common engine pays2h/280 at frozen40%, preview read-only, prior retroactive session supplies actual weekly20h, cancelling cash retains work, historical correction blocks native payroll, native submit/cancel protected')
finally:
 frappe.db.rollback();frappe.db.commit=commit;frappe.enqueue=enqueue;frappe.sendmail=sendmail
 after={d:frappe.db.count(d) for d in counts};assert after==before,(before,after)
 assert settings_before=={d:frappe.db.get_singles_dict(d) for d in settings_before}
 print('RETROACTIVE_ROLLBACK_COUNTS_SETTINGS_UNCHANGED',json.dumps(after));frappe.db.rollback();frappe.destroy()
