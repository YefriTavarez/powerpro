"""DEV-only concurrency test. Commits uniquely named fixtures, deletes only those fixtures.
Global automatic processing must be disabled. No business sources are enrolled.
"""
import json,os,subprocess,sys,time,uuid
from pathlib import Path
import frappe
SITE='igcaribe.fortabs.com'
frappe.init(site=SITE);frappe.connect();frappe.set_user('Administrator')
assert frappe.local.site==SITE and frappe.conf.developer_mode
from powerpro.controllers import automatic_overtime as auto

def local_settings():
 settings=frappe.get_single('DGII Payroll Settings');settings.enable_automatic_overtime_settlement=1
 settings.overtime_exception_roles='System Manager';settings.overtime_auto_payroll_date_policy='Work Date'
 return settings

def forbidden(*a,**kw):raise AssertionError('Outbound effects forbidden')
frappe.sendmail=forbidden;frappe.enqueue=forbidden
if len(sys.argv)>1:
 name,barrier,action=sys.argv[1:]
 auto._settings=local_settings
 # Deliberately establish an old REPEATABLE READ snapshot before the race.
 frappe.db.count('Overtime Authorization')
 Path(barrier+'.'+str(os.getpid())).touch()
 deadline=time.monotonic()+20
 while not Path(barrier).exists():
  assert time.monotonic()<deadline
  time.sleep(.02)
 try:
  if action in {'cancel', 'cancel_call'}:
   doc,call=auto._lock(name)
   target=call if action=='cancel_call' else doc
   target.flags.ignore_permissions=True;target.cancel();result='Cancelled'
  else:
   try:result=auto.process_authorization(name)
   except frappe.ValidationError:
    if frappe.db.get_value(auto.AUTH,name,'docstatus',for_update=True)==2:result='Cancelled'
    else:raise
  frappe.db.commit();print(result)
 finally:frappe.db.rollback();frappe.destroy()
 raise SystemExit()
assert not frappe.db.count(auto.AUTH, {'auto_enrolled':1}), 'No enrolled business records permitted during DEV race tests'
counts=['Employee','Salary Structure Assignment','Overtime Authorization','Overtime Work Call','Additional Salary','Leave Allocation','Leave Ledger Entry','Overtime Compensatory Credit','Overtime Attendance Exception','Leave Period']
baseline={d:frappe.db.count(d) for d in counts}
prefix='AUTO-RACE-DEV-'+uuid.uuid4().hex[:10];empname=prefix+'-EMP';created=[]
checks=[]
try:
 base=frappe.get_doc(auto.AUTH,'AUT-HE-2026-00018')
 emp=frappe.copy_doc(frappe.get_doc('Employee',base.employee));emp.name=empname;emp.docstatus=0;emp.employee_name='DEV Concurrent Overtime';emp.user_id=None;emp.company_email=None;emp.personal_email=None;emp.db_insert();created.append(('Employee',emp.name))
 n=frappe.get_all('Salary Structure Assignment',filters={'employee':base.employee,'docstatus':1},pluck='name',order_by='from_date desc',limit=1)[0]
 ssa=frappe.copy_doc(frappe.get_doc('Salary Structure Assignment',n));ssa.name=prefix+'-SSA';ssa.employee=empname;ssa.docstatus=1;ssa.from_date='2026-01-01';ssa.db_insert();created.append((ssa.doctype,ssa.name))
 if not frappe.db.exists('Leave Period',{'company':emp.company,'is_active':1}):
  period=frappe.get_doc(dict(doctype='Leave Period',company=emp.company,from_date='2026-01-01',to_date='2026-12-31',is_active=1));period.insert(ignore_permissions=True);created.append((period.doctype,period.name))
 def source(key,method,date,start,end):
  call=frappe.copy_doc(frappe.get_doc(auto.CALL,'CONV-HE-2026-00004-1'));call.name=prefix+'-'+key+'-CALL';call.docstatus=1;call.status='Authorized';call.authorization_count=1;call.planned_settlement=method;call.automatic_settlement_enabled=0;call.db_insert();created.append((call.doctype,call.name))
  doc=frappe.copy_doc(base);doc.name=prefix+'-'+key;doc.employee=empname;doc.employee_name=emp.employee_name;doc.docstatus=1;doc.status='Approved';doc.overtime_work_call=call.name;doc.work_date=date;doc.day_classification='Weekly Rest' if frappe.utils.getdate(date).weekday()==6 else 'Regular Workday';doc.authorization_start=date+' '+start;doc.authorization_end=date+' '+end;doc.maximum_hours=2;doc.planned_settlement=method;doc.settlement_status='Pending';doc.reconciliation_status='Scheduled';doc.verified_hours=0;doc.db_insert();created.append((doc.doctype,doc.name))
  auto._enroll(call,local_settings());frappe.db.set_value(auto.AUTH,doc.name,'auto_retry_after','2099-01-01');return doc.name
 cash=source('CASH','Cash','2026-09-08','18:00:00','20:00:00')
 comp1=source('COMP1','Compensatory Rest','2026-09-06','07:00:00','09:00:00')
 comp2=source('COMP2','Compensatory Rest','2026-09-06','09:00:00','11:00:00')
 cancel_call=source('CANCEL-CALL','Compensatory Rest','2026-08-30','07:00:00','09:00:00')
 cancelled=source('CANCEL','Cash','2026-09-09','18:00:00','20:00:00')
 broken=source('BROKEN','Cash','2026-08-31','18:00:00','20:00:00')
 retry=source('RETRY','Cash','2026-09-10','08:00:00','10:00:00')
 frappe.db.commit()
 def race(names,actions=None):
  barrier='/tmp/'+prefix+'-'+uuid.uuid4().hex[:6]
  procs=[subprocess.Popen([sys.executable,__file__,n,barrier,a],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for n,a in zip(names,actions or ['settle']*len(names))]
  deadline=time.monotonic()+15
  while len(list(Path('/tmp').glob(Path(barrier).name+'.*')))<len(procs):
   assert time.monotonic()<deadline,'workers did not reach barrier'
   time.sleep(.05)
  Path(barrier).touch()
  results=[]
  try:
   for p in procs:
    out,err=p.communicate(timeout=25);assert p.returncode==0,(out,err);results.append(out.strip())
  finally:
   for p in procs:
    if p.poll() is None:p.kill();p.wait()
   for f in Path('/tmp').glob(Path(barrier).name+'*'):f.unlink()
  frappe.db.rollback();return results
 assert race([cash,cash])==['Settled','Settled']
 salaries=frappe.get_all('Additional Salary',filters={'ref_doctype':auto.AUTH,'ref_docname':cash,'docstatus':1},pluck='name');assert len(salaries)==1,salaries
 checks.append('two competing cash runs produce exactly one active earning')
 assert race([comp1,comp2])==['Settled','Settled']
 credits=frappe.get_all('Overtime Compensatory Credit',filters={'employee':empname,'docstatus':1},fields=['banked_hours','credited_days']);assert len(credits)==2 and sum(c.banked_hours for c in credits)==4
 allocations=frappe.get_all('Leave Allocation',filters={'employee':empname,'docstatus':1},fields=['name','new_leaves_allocated']);assert len(allocations)==1 and allocations[0].new_leaves_allocated==1,allocations
 entries=frappe.get_all('Leave Ledger Entry',filters={'employee':empname,'transaction_type':'Leave Allocation','docstatus':1},fields=['leaves']);assert sum(r.leaves for r in entries)==1,entries
 checks.append('concurrent credits share one allocation with correct bank and leave ledger')
 results=race([cancelled,cancelled],['settle','cancel'])
 assert 'Cancelled' in results
 assert frappe.db.get_value(auto.AUTH,cancelled,'docstatus')==2
 assert not frappe.db.exists('Additional Salary',{'ref_docname':cancelled,'docstatus':1})
 checks.append('cancellation race leaves no active earning on cancelled source')
 results=race([cancel_call,cancel_call],['settle','cancel_call'])
 assert 'Cancelled' in results
 assert frappe.db.get_value(auto.AUTH,cancel_call,'docstatus')==2
 assert not frappe.db.exists('Overtime Compensatory Credit',{'overtime_authorization':cancel_call,'docstatus':1})
 entries=frappe.get_all('Leave Ledger Entry',filters={'employee':empname,'transaction_type':'Leave Allocation','docstatus':1},fields=['leaves']);assert sum(r.leaves for r in entries)==1,entries
 checks.append('whole Work Call cancellation race reverses only its compensatory credit and retains correct shared balance')
 # Fault after creating real Additional Salary must rollback that entire source;
 # the scheduler can still settle another source and retry the failed one later.
 import powerpro.controllers.overtime_settlement as settlement
 original=settlement._settle_authorization
 def fail_after_create(doc,**kwargs):
  result=original(doc,**kwargs)
  if doc.name==broken:raise RuntimeError('Injected DEV failure after financial creation')
  return result
 auto._settings=local_settings
 # Make RETRY a valid completed regular overtime interval, independent of clock.
 frappe.db.set_value(auto.AUTH,retry,{'work_date':'2026-09-01','authorization_start':'2026-09-01 18:00:00','authorization_end':'2026-09-01 20:00:00'})
 frappe.db.commit()
 frappe.db.set_value(auto.AUTH,broken,'auto_retry_after','2026-01-01');frappe.db.set_value(auto.AUTH,retry,'auto_retry_after','2026-01-01');frappe.db.commit()
 settlement._settle_authorization=fail_after_create
 auto.scheduled_process_due()
 settlement._settle_authorization=original
 assert frappe.db.get_value(auto.AUTH,broken,'auto_status')=='Blocked'
 assert not frappe.db.exists('Additional Salary',{'ref_docname':broken,'docstatus':1})
 # Same employee/week deliberately blocks later dependent regular work.
 assert frappe.db.get_value(auto.AUTH,retry,'auto_status')=='Blocked'
 frappe.db.set_value(auto.AUTH,broken,'auto_retry_after','2026-01-01')
 frappe.db.set_value(auto.AUTH,retry,'auto_retry_after','2026-01-01');frappe.db.commit()
 auto.scheduled_process_due()
 assert frappe.db.get_value(auto.AUTH,broken,'auto_status')=='Settled'
 assert frappe.db.get_value(auto.AUTH,retry,'auto_status')=='Settled'
 checks.append('partial failure rolls back financial output, blocks dependent work and recovers on retry')
 print('DEV_RACE_CHECKS',json.dumps(checks))
finally:
 frappe.db.rollback()
 # Remove only this uniquely named test employee's documents, plus tracked fixtures.
 for dt in ['Additional Salary','Leave Ledger Entry','Leave Allocation','Overtime Compensatory Credit','Overtime Attendance Exception']:
  for n in frappe.get_all(dt,filters={'employee':empname},pluck='name'):created.append((dt,n))
 for dt,n in reversed(created):
  for child in frappe.get_meta(dt).get_table_fields():frappe.db.delete(child.options,{'parent':n,'parenttype':dt})
  for audit in ['Comment','Version','DocShare']:
   filters={'ref_doctype':dt,'docname':n} if audit=='Version' else {'share_doctype':dt,'share_name':n} if audit=='DocShare' else {'reference_doctype':dt,'reference_name':n}
   frappe.db.delete(audit,filters)
  frappe.db.delete(dt,{'name':n})
 frappe.db.commit()
 after={d:frappe.db.count(d) for d in counts};print('COUNTS_UNCHANGED',after==baseline,after);assert after==baseline
 frappe.destroy()
