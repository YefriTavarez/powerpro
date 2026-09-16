"""Development controller integration only; no schema changes, all fixtures rolled back.

Exercises real Frappe validation/before_submit without persisting the new-schema
adjustment. Full form save/readback remains a post-deployment acceptance check.
"""
import json,sys,uuid
from pathlib import Path
from unittest.mock import patch
import frappe
frappe.init(site='igcaribe.fortabs.com');frappe.connect()
assert frappe.conf.developer_mode and frappe.local.site=='igcaribe.fortabs.com'
# Load reviewed code from a temporary tree, leaving the Development checkout alone.
import powerpro
powerpro.__path__.insert(0,str(Path(__file__).resolve().parents[1]/'powerpro'))
for name in list(sys.modules):
 if name.startswith('powerpro.'):
  del sys.modules[name]
from powerpro.power_pro.doctype.retroactive_overtime_adjustment.retroactive_overtime_adjustment import RetroactiveOvertimeAdjustment
from powerpro.controllers import retroactive_documentation as history
from powerpro.controllers.overtime_cash_settlement import create_cash_settlement_for_source
from frappe.core.doctype.file.file import File
frappe.set_user('Administrator')
counts=['Employee','Retroactive Overtime Adjustment','File','Additional Salary','Salary Slip','Employee Checkin','Overtime Compensatory Credit','Overtime Settlement Election']
before={dt:frappe.db.count(dt) for dt in counts}
settings_before=frappe.db.get_singles_dict('DGII Payroll Settings')
original=(frappe.db.commit,frappe.sendmail,frappe.enqueue)
def forbidden(*a,**k):raise AssertionError('Commit or outbound effect forbidden')
frappe.db.commit=frappe.sendmail=frappe.enqueue=forbidden
prefix='HISTORY-DEV-'+uuid.uuid4().hex[:10]
try:
 frappe.db.set_single_value('DGII Payroll Settings',{'enable_overtime_authorization':1,'enable_retroactive_overtime_adjustment':1,
  'retroactive_overtime_from_date':'2026-08-01','retroactive_overtime_to_date':'2026-08-31','retroactive_overtime_submission_deadline':'2026-12-31'})
 base=frappe.get_all('Employee',filters={'status':'Active','overtime_eligible':1},pluck='name',limit=1)[0]
 employee=frappe.copy_doc(frappe.get_doc('Employee',base))
 employee.docstatus=0;employee.name=prefix;employee.employee_name='Synthetic History';employee.overtime_approver='Administrator'
 employee.overtime_eligible=1;employee.user_id=None;employee.company_email=None;employee.personal_email=None
 employee.db_insert()
 def document(kind,start,end,maximum,break_start=None,break_end=None):
  doc=RetroactiveOvertimeAdjustment(dict(doctype=history.DT,name=prefix+'-'+kind,owner='Administrator',employee=employee.name,
   docstatus=0,work_date=start[:10],authorization_start=start,authorization_end=end,maximum_hours=maximum,
   reason='Synthetic DEV controller test',exception_justification='Synthetic fixture, rolled back',planned_settlement='Cash',
   settlement_payroll_date='2026-08-30',historical_documentation=1,historical_disposition=kind,
   historical_reference='Synthetic PDF; operator confirms previously paid; estimated break',historical_acknowledged=1,
   historical_source_file='/private/files/'+prefix+'.pdf',historical_break_start=break_start,historical_break_end=break_end,
   historical_break_estimated=bool(break_start),reconciliation_engine='Verified Checkins'))
  file=frappe.get_doc(dict(doctype='File',docstatus=0,name=prefix+'-'+kind,file_name='synthetic.pdf',is_private=1,
   file_url=doc.historical_source_file,attached_to_doctype=history.DT,attached_to_name=doc.name));file.db_insert()
  doc.validate()
  assert doc.approver=='Administrator' and doc.reconciliation_engine=='Documentary'
  with patch.object(File,'get_content',return_value=b'Synthetic test PDF'):
   doc.before_submit()
  return doc
 night=document('Already Paid','2026-08-16 18:00:00','2026-08-17 06:00:00',11,'2026-08-16 21:00:00','2026-08-16 22:00:00')
 morning=document('Ordinary Work','2026-08-14 08:00:00','2026-08-14 09:45:00',1.75)
 for doc,hours in [(night,11),(morning,1.75)]:
  assert doc.status=='Documented' and doc.historical_hours==hours and doc.verified_hours==0
  assert doc.settlement_status=='Not Applicable' and doc.settlement_amount==0
  assert json.loads(doc.historical_snapshot)['recorded_by']=='Administrator'
  try:create_cash_settlement_for_source(doc,{})
  except frappe.ValidationError:pass
  else:raise AssertionError('Documentary payroll was not blocked')
 assert all(frappe.db.count(dt)==before[dt] for dt in counts if dt not in ['Employee','File'])
 print(json.dumps({'ok':True,'native_validate_and_before_submit':True,'hours':[11,1.75],'financial_writes':False,'schema_changes':False}))
finally:
 frappe.db.rollback()
 frappe.db.commit,frappe.sendmail,frappe.enqueue=original
 assert {dt:frappe.db.count(dt) for dt in counts}==before
 assert frappe.db.get_singles_dict('DGII Payroll Settings')==settings_before
 print(json.dumps({'rollback_verified':True}))
 frappe.destroy()
