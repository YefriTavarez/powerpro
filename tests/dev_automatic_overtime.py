"""Explicit DEV-only integration check; synthetic sources, financial docs rolled back.
Run from a bench sites directory: ../env/bin/python /path/to/this/file.py
"""
import json
import uuid
import frappe

SITE='igcaribe.fortabs.com'
frappe.init(site=SITE);frappe.connect();frappe.set_user('Administrator')
assert frappe.local.site == SITE and frappe.conf.developer_mode
from powerpro.controllers import automatic_overtime as auto
from powerpro.controllers.overtime_cash_settlement import _get_linked_additional_salaries
from powerpro.controllers.overtime_compensatory_settlement import _get_bank_totals
from powerpro.controllers.overtime_settlement import settlement_hours
counts=['Employee','Overtime Authorization','Overtime Work Call','Employee Checkin','Salary Slip','Additional Salary','Leave Allocation','Overtime Compensatory Credit','Leave Application','Leave Ledger Entry','Overtime Attendance Exception']
baseline={dt:frappe.db.count(dt) for dt in counts}
prefix='AUTO-OT-DEV-'+uuid.uuid4().hex[:10]
checks=[]
def forbidden(*a,**kw):raise AssertionError('No commits or outbound effects in rollback test')
commit,sendmail,enqueue=frappe.db.commit,frappe.sendmail,frappe.enqueue
frappe.db.commit=forbidden;frappe.sendmail=forbidden;frappe.enqueue=forbidden
try:
 frappe.db.set_single_value('DGII Payroll Settings',{'enable_automatic_overtime_settlement':1,'overtime_exception_roles':'System Manager','overtime_auto_payroll_date_policy':'Work Date'})
 base=frappe.get_doc('Overtime Authorization','AUT-HE-2026-00018')
 employee=frappe.copy_doc(frappe.get_doc('Employee',base.employee));employee.name=prefix+'-EMP';employee.employee_name='DEV Overtime Test';employee.user_id=None;employee.company_email=None;employee.personal_email=None;employee.db_insert()
 original=frappe.get_all('Salary Structure Assignment',filters={'employee':base.employee,'docstatus':1},pluck='name',order_by='from_date desc',limit=1)
 assert original,'No source salary assignment'
 assignment=frappe.copy_doc(frappe.get_doc('Salary Structure Assignment',original[0]));assignment.name=prefix+'-SSA';assignment.employee=employee.name;assignment.docstatus=1;assignment.from_date='2026-01-01';assignment.db_insert()
 def source(key,method,date,start,end):
  call=frappe.copy_doc(frappe.get_doc('Overtime Work Call','CONV-HE-2026-00004-1'));call.name=prefix+'-'+key+'-CALL';call.docstatus=1;call.status='Authorized';call.authorization_count=1;call.planned_settlement=method;call.automatic_settlement_enabled=0;call.db_insert()
  doc=frappe.copy_doc(base);doc.name=prefix+'-'+key;doc.employee=employee.name;doc.employee_name=employee.employee_name;doc.docstatus=1;doc.status='Approved';doc.overtime_work_call=call.name;doc.work_date=date;doc.authorization_start=date+' '+start;doc.authorization_end=date+' '+end;doc.maximum_hours=(frappe.utils.get_datetime(doc.authorization_end)-frappe.utils.get_datetime(doc.authorization_start)).total_seconds()/3600;doc.planned_settlement=method;doc.settlement_status='Pending';doc.reconciliation_status='Scheduled';doc.verified_hours=0;doc.db_insert()
  auto._enroll(call,auto._settings())
  return frappe.get_doc(auto.AUTH,doc.name),call
 def current(doc):return frappe.get_doc(auto.AUTH,doc.name,for_update=True)
 def exception(doc,action,intervals=None):
  args=dict(authorization=doc.name,action=action,reason='DEV rollback integration',intervals=intervals)
  preview=auto.preview_attendance_exception(**args)
  out=auto.record_attendance_exception(**args,token=preview['token'])
  assert auto.record_attendance_exception(**args,token=preview['token'])['exception']==out['exception']
  return out
 cash,call=source('CASH','Cash','2026-09-08','18:00:00','20:00:00')
 assert auto.process_authorization(cash.name)=='Settled'
 cash=current(cash);assert cash.verified_hours==0 and cash.presumed_hours==2,cash.as_dict()
 refs=_get_linked_additional_salaries(cash,docstatus=1);assert refs
 assert auto.process_authorization(cash.name)=='Settled'
 assert refs==_get_linked_additional_salaries(cash,docstatus=1)
 checks.append('cash creation, presumed audit and idempotent processing')
 out=exception(cash,'Correct Worked Hours',[{'start':'2026-09-08 18:00:00','end':'2026-09-08 19:00:00'}]);assert out['status']=='Applied',out
 cash=current(cash);assert cash.verified_hours==1 and cash.presumed_hours==0
 assert all(frappe.db.get_value('Additional Salary',n,'docstatus')==2 for n in refs)
 refs=_get_linked_additional_salaries(cash,docstatus=1);assert refs
 checks.append('cash correction cancels only original inputs and creates replacement')
 # Submitted financial evidence fixture exercises real lookup and keeps outputs untouched.
 slip=frappe.new_doc('Salary Slip');slip.name=prefix+'-SLIP';slip.employee=employee.name;slip.company=employee.company;slip.docstatus=1;slip.db_insert()
 detail=frappe.new_doc('Salary Detail');detail.name=prefix+'-DETAIL';detail.parent=slip.name;detail.parenttype='Salary Slip';detail.parentfield='earnings';detail.additional_salary=refs[0];detail.db_insert()
 out=exception(cash,'Mark Absent');assert out['status']=='Correction Pending',out
 assert slip.name in out['blockers']
 assert _get_linked_additional_salaries(cash,docstatus=1)==refs
 assert current(cash).settlement_amount==cash.settlement_amount
 frappe.db.set_value('Salary Slip',slip.name,'docstatus',2)
 out=auto.retry_attendance_exception(cash.name);assert out['status']=='Applied',out
 assert current(cash).auto_status=='Excluded' and not _get_linked_additional_salaries(cash,docstatus=1)
 checks.append('submitted salary blocks reversal; retry after controlled cancellation excludes only source')
 comp,call=source('COMP','Compensatory Rest','2026-09-06','07:00:00','12:00:00')
 assert auto.process_authorization(comp.name)=='Settled'
 comp=current(comp);assert comp.presumed_hours==5 and comp.verified_hours==0
 credit=comp.compensatory_credit;allocation=comp.leave_allocation;assert credit and allocation
 assert frappe.db.get_value('Leave Allocation',allocation,'new_leaves_allocated')==1
 out=exception(comp,'Correct Worked Hours',[{'start':'2026-09-06 07:00:00','end':'2026-09-06 11:00:00'}]);assert out['status']=='Applied',out
 comp=current(comp);assert comp.verified_hours==4 and frappe.db.get_value('Overtime Compensatory Credit',credit,'docstatus')==2
 checks.append('compensatory credit, allocation and corrected replacement')
 leave=frappe.new_doc('Leave Application');leave.name=prefix+'-LEAVE';leave.employee=employee.name;leave.leave_type=auto._settings().overtime_compensatory_leave_type;leave.from_date='2026-09-09';leave.to_date='2026-09-09';leave.total_leave_days=1;leave.status='Approved';leave.docstatus=1;leave.db_insert()
 out=exception(comp,'Mark Absent');assert out['status']=='Correction Pending',out
 assert leave.name in out['blockers'] and allocation in out['blockers']
 assert frappe.db.get_value('Overtime Compensatory Credit',comp.compensatory_credit,'docstatus')==1
 assert frappe.db.get_value('Leave Allocation',allocation,'new_leaves_allocated')==1
 frappe.db.set_value('Leave Application',leave.name,'docstatus',2)
 out=auto.retry_attendance_exception(comp.name);assert out['status']=='Applied',out
 assert frappe.db.get_value('Leave Allocation',allocation,'new_leaves_allocated')==0
 checks.append('consumed leave blocks reversal with linked evidence; controlled retry adjusts bank')
 absent,call=source('ABSENT','Cash','2026-09-09','18:00:00','20:00:00')
 out=exception(absent,'Mark Absent');assert out['status']=='Applied'
 assert auto.process_authorization(absent.name)=='Excluded'
 assert not _get_linked_additional_salaries(absent,docstatus=1)
 checks.append('pre-settlement absence creates no financial outputs')
 future,call=source('FUTURE','Cash','2026-09-13','18:00:00','20:00:00')
 assert auto.process_authorization(future.name)=='Queued'
 frappe.set_user('Guest')
 try:auto.preview_attendance_exception(future.name,'Cancel Participation','Unauthorized test')
 except frappe.PermissionError:pass
 else:raise AssertionError('Guest permitted')
 frappe.set_user('Administrator')
 out=exception(future,'Cancel Participation');assert out['status']=='Applied'
 checks.append('future windows queue; unauthorized user denied; participation can be cancelled')
 print('DEV_AUTOMATIC_CHECKS',json.dumps(checks))
finally:
 frappe.db.rollback();frappe.db.commit=commit;frappe.sendmail=sendmail;frappe.enqueue=enqueue
 after={dt:frappe.db.count(dt) for dt in counts}
 print('COUNTS_UNCHANGED',after==baseline,json.dumps(after));assert after==baseline
 frappe.db.rollback();frappe.destroy()
