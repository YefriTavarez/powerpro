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
 'Overtime Authorization','Overtime Reconciliation Run','Additional Salary','Salary Slip']
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
 def draft(day):
  doc=frappe.get_doc({'doctype':DT,'employee':employee.name,'work_date':day,'authorization_start':day+' 18:00:00',
   'authorization_end':day+' 20:00:00','maximum_hours':2,'reason':'DEV historical work','exception_justification':'DEV historical exception',
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
 print('RETROACTIVE_EVIDENCE_ACCEPTANCE: missing exit blocks, common engine pays2h/280 at frozen40%, preview read-only, prior retroactive session supplies actual weekly20h, cancelling cash retains work, historical correction blocks native payroll, native submit/cancel protected')
finally:
 frappe.db.rollback();frappe.db.commit=commit;frappe.enqueue=enqueue;frappe.sendmail=sendmail
 after={d:frappe.db.count(d) for d in counts};assert after==before,(before,after)
 assert settings_before=={d:frappe.db.get_singles_dict(d) for d in settings_before}
 print('RETROACTIVE_ROLLBACK_COUNTS_SETTINGS_UNCHANGED',json.dumps(after));frappe.db.rollback();frappe.destroy()
