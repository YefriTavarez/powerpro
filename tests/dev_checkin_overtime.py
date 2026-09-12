"""DEV-only integration acceptance. Real documents and writes, all rolled back.
Run via bench env from sites. Never execute against production.
"""
import json,uuid
from unittest.mock import patch
import frappe
from frappe.utils import get_datetime
SITE='igcaribe.fortabs.com'
frappe.init(site=SITE);frappe.connect();frappe.set_user('Administrator')
assert frappe.local.site==SITE and frappe.conf.developer_mode
from powerpro.controllers import checkin_overtime as evidence
from powerpro.controllers.overtime_settlement import _validate_ready
prefix='EVIDENCE-DEV-'+uuid.uuid4().hex[:10]
counts=['Employee','Shift Type','Employee Checkin','Overtime Authorization','Overtime Work Call','Overtime Reconciliation Run','Additional Salary','Leave Allocation','Salary Slip']
before={d:frappe.db.count(d) for d in counts}
original_settings=frappe.db.get_singles_dict('DGII Payroll Settings')
commit,sendmail,enqueue=frappe.db.commit,frappe.sendmail,frappe.enqueue
checks=[]
def forbidden(*args,**kw):raise AssertionError('Outbound or commit attempted in rollback fixture')
frappe.db.commit=forbidden;frappe.sendmail=forbidden;frappe.enqueue=forbidden
try:
 frappe.db.set_single_value('DGII Payroll Settings',{'enable_checkin_overtime_reconciliation':1,'checkin_overtime_effective_from':'2026-09-01'})
 base=frappe.get_doc('Overtime Authorization','AUT-HE-2026-00018')
 employee=frappe.copy_doc(frappe.get_doc('Employee',base.employee));employee.name=prefix+'-EMP';employee.docstatus=0
 employee.employee_name='DEV Evidence';employee.user_id=None;employee.company_email=None;employee.personal_email=None;employee.status='Active'
 shift=frappe.copy_doc(frappe.get_doc('Shift Type','Diurna Extendida'));shift.name=prefix+'-SHIFT';shift.enable_auto_attendance=0
 shift.determine_check_in_and_check_out='Alternating entries as IN and OUT during the same shift';shift.working_hours_calculation_based_on='Every Valid Check-in and Check-out'
 shift.last_sync_of_checkin='2026-09-16 08:00:00';shift.db_insert()
 employee.default_shift=shift.name;employee.db_insert()
 call=frappe.copy_doc(frappe.get_doc('Overtime Work Call','CONV-HE-2026-00004-1'))
 call.name=None;call.docstatus=0;call.company=employee.company;call.from_date='2026-09-15';call.to_date='2026-09-15';call.planned_settlement='Cash'
 call.automation_mode='Verified Checkins';call.evidence_auto_settle=0
 call.set('employees',[]);call.append('employees',{'employee':employee.name})
 call.set('dates',[]);call.append('dates',{'work_date':'2026-09-15','start_time':'18:00:00','end_time':'20:00:00','requested_hours':2})
 call.insert(ignore_permissions=True);call.flags.ignore_permissions=True;call.submit()
 names=frappe.get_all('Overtime Authorization',filters={'overtime_work_call':call.name},pluck='name');assert len(names)==1
 name=names[0];auth=frappe.get_doc('Overtime Authorization',name)
 assert auth.evidence_enrolled and not auth.auto_enrolled and auth.evidence_status=='Pending'
 checks.append('normal Work Call submit generated and enrolled verified mode without presumed enrollment')
 def punch(clock,kind):
  doc=frappe.get_doc({'doctype':'Employee Checkin','employee':employee.name,'time':'2026-09-15 '+clock,'log_type':kind,'skip_auto_attendance':0})
  doc.insert(ignore_permissions=True);return doc
 first=punch('08:00:00','IN');punch('12:00:00','OUT');punch('13:00:00','IN')
 with patch.object(evidence,'now_datetime',return_value=get_datetime('2026-09-15 21:00:00')):
  assert evidence.process_authorization(name)=='Needs Review'
  assert frappe.db.get_value('Overtime Authorization',name,'verified_hours')==0
  last=punch('20:00:00','OUT')
  assert evidence.process_authorization(name)=='Verified'
  auth=frappe.get_doc('Overtime Authorization',name)
  assert auth.actual_start==get_datetime('2026-09-15 18:00:00') and auth.actual_end==get_datetime('2026-09-15 20:00:00')
  assert auth.verified_hours==2 and auth.presumed_hours==0 and auth.reconciliation_source=='Employee Checkin'
  assert frappe.db.get_value('Overtime Work Call',call.name,'verified_hours')==2
  checks.append('late exit changes review to actual 18:00-20:00 / 2 hours and syncs Work Call')
  audit_count=frappe.db.count('Overtime Reconciliation Run',{'authorization':name})
  assert evidence.process_authorization(name)=='Verified'
  assert frappe.db.count('Overtime Reconciliation Run',{'authorization':name})==audit_count
  checks.append('idempotent evaluation has no duplicate immutable run')
  try:_validate_ready(auth)
  except frappe.ValidationError:pass
  else:raise AssertionError('Unapproved policy allowed settlement')
  checks.append('pending payroll policy blocks settlement independently of real-hour persistence')
  frozen=auth.evidence_snapshot
  last.time='2026-09-15 19:00:00';last.save(ignore_permissions=True)
  assert evidence.process_authorization(name)=='Needs Review'
  assert evidence.process_authorization(name)=='Needs Review'
  auth=frappe.get_doc('Overtime Authorization',name)
  assert auth.verified_hours==2 and auth.evidence_snapshot==frozen
  checks.append('post-verification source changes preserve frozen hours through repeated retries')
  auth.evidence_status='Verified'
  try:auth.save(ignore_permissions=True)
  except frappe.ValidationError:pass
  else:raise AssertionError('Generic save forged evidence status')
  checks.append('generic document save cannot forge service-owned evidence')
  frappe.db.set_value('Overtime Authorization',name,{'reconciliation_source':'Manual Verification','verified_hours':1})
  assert evidence.process_authorization(name)=='Manual Verification'
  assert frappe.db.get_value('Overtime Authorization',name,'verified_hours')==1
  checks.append('explicit HR verification is not overwritten by checkin retries')
 frappe.set_user('Guest')
 try:evidence.process_now(name)
 except frappe.PermissionError:pass
 else:raise AssertionError('Guest triggered a write')
 frappe.set_user('Administrator')
 print('DEV_CHECKIN_ACCEPTANCE',json.dumps(checks))
finally:
 frappe.db.rollback();frappe.db.commit=commit;frappe.sendmail=sendmail;frappe.enqueue=enqueue
 after={d:frappe.db.count(d) for d in counts}
 assert before==after,(before,after)
 assert frappe.db.get_singles_dict('DGII Payroll Settings')==original_settings
 print('ROLLBACK_COUNTS_UNCHANGED',json.dumps(after))
 frappe.db.rollback();frappe.destroy()
