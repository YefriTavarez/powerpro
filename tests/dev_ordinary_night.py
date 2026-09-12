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
counts=['Employee','Shift Type','Employee Checkin','Overtime Authorization','Overtime Work Call','Overtime Reconciliation Run','Overtime Pay Policy',DT,'Additional Salary','Salary Slip','Salary Structure Assignment']
before={dt:frappe.db.count(dt) for dt in counts}
settings_before={dt:frappe.db.get_singles_dict(dt) for dt in ['DGII Payroll Settings','Payroll Settings']}
commit,enqueue,sendmail=frappe.db.commit,frappe.enqueue,frappe.sendmail

def forbidden(*a,**kw):raise AssertionError('Commit or outbound effect forbidden')
frappe.db.commit=forbidden;frappe.enqueue=forbidden;frappe.sendmail=forbidden
prefix='NIGHT-DEV-'+uuid.uuid4().hex[:8]
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
  'night_basis':'Clock overlap','premium_combination':'Additive on base hour','enable_compensatory':0})
 policy.insert(ignore_permissions=True);policy.flags.ignore_permissions=True;policy.submit()
 def punch(stamp,kind):
  doc=frappe.get_doc({'doctype':'Employee Checkin','employee':employee.name,'time':stamp,'log_type':kind});doc.insert(ignore_permissions=True);return doc
 first=punch('2026-09-14 18:00:00','IN');last=punch('2026-09-15 02:00:00','OUT')
 def draft():
  doc=frappe.get_doc({'doctype':DT,'employee':employee.name,'work_date':'2026-09-14','settlement_payroll_date':'2026-09-15','review_reference':'DEV synthetic reference'})
  doc.insert(ignore_permissions=True);doc.flags.ignore_permissions=True;return doc
 with patch.object(night,'now_datetime',return_value=get_datetime('2026-09-16 10:00:00')):
  doc=draft();assert doc.evidence_status=='Verified' and doc.night_hours==5 and doc.settlement_amount==75
  doc.submit();doc.reload();assert doc.settlement_status=='Created'
  refs=_get_linked_additional_salaries(doc,docstatus=1);assert len(refs)==1
  assert frappe.db.count('Overtime Authorization')==before['Overtime Authorization']
  duplicate=draft()
  try:duplicate.submit()
  except (frappe.ValidationError,frappe.UniqueValidationError):pass
  else:raise AssertionError('Duplicate ordinary night settlement accepted')
  salary=frappe.get_doc('Additional Salary',refs[0]);salary.flags.ignore_permissions=True
  try:salary.cancel()
  except frappe.ValidationError:pass
  else:raise AssertionError('Direct salary cancellation bypassed source')
  from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
  slip=make_salary_slip(assignment.salary_structure,employee=employee.name,posting_date='2026-09-15',ignore_permissions=True)
  slip.insert(ignore_permissions=True);slip.flags.ignore_permissions=True
  last.time='2026-09-15 01:00:00';last.save(ignore_permissions=True)
  assert night.get_status(doc.name)['state']=='Needs Review'
  try:slip.submit()
  except frappe.ValidationError:pass
  else:raise AssertionError('Payroll accepted stale night evidence')
  last.time='2026-09-15 02:00:00';last.save(ignore_permissions=True)
  slip.reload();slip.flags.ignore_permissions=True;slip.submit();doc.reload()
  assert doc.settlement_status=='Payroll Submitted' and doc.settlement_salary_slip==slip.name
  try:doc.cancel()
  except frappe.ValidationError:pass
  else:raise AssertionError('Source cancellation bypassed submitted payroll')
  slip.cancel();doc.reload();doc.flags.ignore_permissions=True;doc.cancel();doc.reload()
  assert doc.docstatus==2 and not doc.active_claim and frappe.db.get_value('Additional Salary',refs[0],'docstatus')==2
  corrected=draft();corrected.submit()
  assert len(_get_linked_additional_salaries(corrected,docstatus=1))==1
  corrected.flags.ignore_permissions=True;corrected.cancel()
  # A separate ordinary+OT journey: the same evidence has one premium in each
  # category. Cancelled fixtures above have no remaining active claim.
  next_shift=frappe.copy_doc(shift);next_shift.name=prefix+'-SECOND-SHIFT';next_shift.docstatus=0;next_shift.start_time='16:00:00';next_shift.end_time='22:00:00';next_shift.db_insert()
  employee.db_set('default_shift',next_shift.name)
  frappe.db.value_cache.clear()
  first.reload();first.shift=None;first.save(ignore_permissions=True)
  last.reload();last.time='2026-09-14 23:00:00';last.shift=None;last.save(ignore_permissions=True)
  from powerpro.controllers import checkin_overtime as evidence
  call=frappe.copy_doc(frappe.get_doc('Overtime Work Call','CONV-HE-2026-00004-1'));call.name=None;call.docstatus=0
  call.company=employee.company;call.from_date='2026-09-14';call.to_date='2026-09-14';call.planned_settlement='Cash'
  call.automation_mode='Verified Checkins';call.evidence_auto_settle=1
  call.set('employees',[]);call.append('employees',{'employee':employee.name})
  call.set('dates',[]);call.append('dates',{'work_date':'2026-09-14','start_time':'22:00:00','end_time':'23:00:00','requested_hours':1})
  call.insert(ignore_permissions=True);call.flags.ignore_permissions=True;call.submit()
  auth_name=frappe.db.get_value('Overtime Authorization',{'overtime_work_call':call.name},'name')
  with patch.object(evidence,'now_datetime',return_value=get_datetime('2026-09-16 10:00:00')):
   result=evidence.process_authorization(auth_name)
   auth=frappe.get_doc('Overtime Authorization',auth_name)
   assert result=='Verified' and not auth.evidence_settlement_ready,(result,auth.evidence_issues)
   ordinary=draft();assert ordinary.night_hours==1 and ordinary.settlement_amount==15
   ordinary.submit()
   result=evidence.process_authorization(auth_name);auth.reload()
   assert result=='Frozen',(result,auth.evidence_issues)
   assert auth.night_hours==1 and auth.settlement_amount==150,(auth.night_hours,auth.settlement_amount)
   snapshot=frappe.parse_json(auth.evidence_snapshot)
   assert snapshot['ordinary_night_settlement']['name']==ordinary.name
   try:ordinary.cancel()
   except frappe.ValidationError:pass
   else:raise AssertionError('Ordinary coverage could be cancelled before linked OT')
   call.reload();call.flags.ignore_permissions=True;call.cancel()
   ordinary.reload();ordinary.flags.ignore_permissions=True;ordinary.cancel()
  # Missing/invalid exit: certify once through the real HR review API, then
  # reuse it for ordinary night and resume the pending OT without changing source.
  frappe.db.set_single_value('DGII Payroll Settings','enable_manual_overtime_verification',1)
  last.reload();last.skip_auto_attendance=1;last.save(ignore_permissions=True)
  manual_call=frappe.copy_doc(call);manual_call.name=None;manual_call.docstatus=0
  from powerpro.controllers.automatic_overtime import CALL_FIELDS
  for field in CALL_FIELDS+('evidence_reconciliation_enabled',):manual_call.set(field,None)
  manual_call.insert(ignore_permissions=True);manual_call.flags.ignore_permissions=True;manual_call.submit()
  manual_name=frappe.db.get_value('Overtime Authorization',{'overtime_work_call':manual_call.name},'name')
  from powerpro.controllers import checkin_overtime_review as review
  with patch.object(evidence,'now_datetime',return_value=get_datetime('2026-09-16 10:00:00')):
   assert evidence.process_authorization(manual_name)=='Needs Review'
   declaration={'full_session':True,'reference':'DEV supervisor signed complete session',
       'intervals':[{'start':'2026-09-14 18:00:00','end':'2026-09-14 23:00:00'}]}
   punch_count=frappe.db.count('Employee Checkin')
   preview=review.preview_review(manual_name,'DEV missing exit confirmed by supervisor',manual_declaration=declaration)
   review.apply_review(manual_name,'DEV missing exit confirmed by supervisor',preview['token'],manual_declaration=declaration)
   manual=frappe.get_doc('Overtime Authorization',manual_name)
   assert manual.reconciliation_source=='Manual Verification' and not manual.evidence_settlement_ready
   frozen=frappe.parse_json(manual.evidence_snapshot);identity=(manual.reconciled_by,manual.reconciled_on)
   manual_night=draft()
   night_snapshot=frappe.parse_json(manual_night.evidence_snapshot)
   assert night_snapshot['input']['certified_session']['authorization']==manual.name
   assert manual_night.night_hours==1 and manual_night.settlement_amount==15
   # A changed raw punch cannot silently reuse HR's declaration.
   frappe.db.savepoint('night_manual_stale')
   last.skip_auto_attendance=0;last.save(ignore_permissions=True)
   try:manual_night.submit()
   except frappe.ValidationError:pass
   else:raise AssertionError('Night settlement accepted changed manual evidence')
   frappe.db.rollback(save_point='night_manual_stale');manual_night.reload();manual_night.flags.ignore_permissions=True
   manual_night.submit()
   assert evidence.process_authorization(manual.name)=='Frozen'
   manual.reload();assert manual.reconciliation_source=='Manual Verification' and manual.settlement_amount==150
   current=frappe.parse_json(manual.evidence_snapshot)
   assert current['review']==frozen['review'] and current['snapshot']==frozen['snapshot']
   assert identity==(manual.reconciled_by,manual.reconciled_on)
   assert current['ordinary_night_settlement']['name']==manual_night.name
   salary_count=frappe.db.count('Additional Salary')
   assert evidence.process_authorization(manual.name)=='Frozen'
   assert frappe.db.count('Additional Salary')==salary_count and frappe.db.count('Employee Checkin')==punch_count
   # Payroll must validate both documents through their actual native lifecycle.
   manual_slip=make_salary_slip(assignment.salary_structure,employee=employee.name,posting_date='2026-09-15',ignore_permissions=True)
   manual_slip.insert(ignore_permissions=True);manual_slip.flags.ignore_permissions=True;manual_slip.submit()
   manual.reload();manual_night.reload()
   assert manual.settlement_status==manual_night.settlement_status=='Payroll Submitted'
   manual_slip.cancel();manual_call.reload();manual_call.flags.ignore_permissions=True;manual_call.cancel()
   manual_night.reload();manual_night.flags.ignore_permissions=True;manual_night.cancel()
  print('NIGHT_MANUAL_ACCEPTANCE: one HR declaration reused, 15 ordinary plus 150 OT, unchanged source/actor/punches, stale source rejected, idempotent resume and native payroll/cancel')
 print('NIGHT_ACCEPTANCE: no OT document, verified 5 ordinary night hours / 75 premium, duplicate and direct-cancel guards, stale evidence blocks native payroll, native submit/cancel, corrected replacement')
 print('NIGHT_OT_ACCEPTANCE: ordinary premium 15 plus OT 135 and extra night premium 15, distinct sources and protected cancellation order')
finally:
 frappe.db.rollback();frappe.db.commit=commit;frappe.enqueue=enqueue;frappe.sendmail=sendmail
 after={dt:frappe.db.count(dt) for dt in counts};assert before==after,(before,after)
 assert settings_before=={dt:frappe.db.get_singles_dict(dt) for dt in settings_before}
 print('NIGHT_ROLLBACK_UNCHANGED',json.dumps(after));frappe.db.rollback();frappe.destroy()
