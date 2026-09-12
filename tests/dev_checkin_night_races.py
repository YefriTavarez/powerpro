"""DEV-only concurrent evidence/night settlement, with uniquely owned fixtures.

Needs committed fixtures for independent MariaDB connections. Global processing
stays disabled in the database; only these processes see an in-memory opt-in.
Finally removes exactly this employee's test rows and tracked setup documents.
"""
import json,os,subprocess,sys,time,uuid
from pathlib import Path
import frappe
from frappe.utils import get_datetime
SITE='igcaribe.fortabs.com'
frappe.init(site=SITE);frappe.connect();frappe.set_user('Administrator')
assert frappe.local.site==SITE and frappe.conf.developer_mode
from powerpro.controllers import checkin_overtime as evidence,ordinary_night as night

def forbidden(*args,**kwargs):raise AssertionError('Outbound effects forbidden in race fixture')
frappe.sendmail=forbidden;frappe.enqueue=forbidden
get_single=frappe.get_single

def settings(doctype,*args,**kwargs):
 doc=get_single(doctype,*args,**kwargs)
 if doctype=='DGII Payroll Settings':
  doc.enable_checkin_overtime_reconciliation=1;doc.checkin_overtime_effective_from='2026-09-01'
 return doc

if len(sys.argv)>1:
 name,barrier=sys.argv[1:]
 assert name.startswith('CHECKIN-RACE-DEV-')
 assert not frappe.db.get_single_value('DGII Payroll Settings','enable_checkin_overtime_reconciliation')
 frappe.get_single=settings
 evidence.now_datetime=night.now_datetime=lambda:get_datetime('2026-09-16 10:00:00')
 # Establish a stale REPEATABLE READ snapshot before acquiring business locks.
 frappe.db.count('Ordinary Night Settlement')
 Path(barrier+'.'+str(os.getpid())).touch()
 deadline=time.monotonic()+20
 while not Path(barrier).exists():
  assert time.monotonic()<deadline,'barrier never opened'
  time.sleep(.02)
 try:
  result=evidence.process_authorization(name)
  frappe.db.commit();print(json.dumps({'status':result}))
 finally:frappe.db.rollback();frappe.destroy()
 raise SystemExit()

assert not frappe.db.get_single_value('DGII Payroll Settings','enable_checkin_overtime_reconciliation')
assert not frappe.db.count('Overtime Authorization',{'evidence_enrolled':1})
assert not frappe.db.count('Overtime Pay Policy',{'docstatus':1})
types=['Employee','Shift Type','Employee Checkin','Salary Structure Assignment','Overtime Pay Policy',
       'Overtime Work Call','Overtime Authorization','Ordinary Night Settlement','Additional Salary','Overtime Reconciliation Run','Salary Slip']
baseline={d:frappe.db.count(d) for d in types}
settings_before=frappe.db.get_singles_dict('DGII Payroll Settings')
prefix='CHECKIN-RACE-DEV-'+uuid.uuid4().hex[:10];employee_name=prefix+'-EMP';owned=[]
procs=[];barrier='/tmp/'+prefix+'-barrier'
try:
 base=frappe.get_doc('Overtime Authorization','AUT-HE-2026-00018')
 shift=frappe.copy_doc(frappe.get_doc('Shift Type','Diurna Extendida'))
 shift.name=prefix+'-SHIFT';shift.docstatus=0;shift.start_time='16:00:00';shift.end_time='22:00:00';shift.enable_auto_attendance=0
 shift.begin_check_in_before_shift_start_time=0;shift.allow_check_out_after_shift_end_time=0
 shift.determine_check_in_and_check_out='Alternating entries as IN and OUT during the same shift'
 shift.working_hours_calculation_based_on='Every Valid Check-in and Check-out';shift.last_sync_of_checkin='2026-09-30 23:00:00'
 shift.db_insert();owned.append((shift.doctype,shift.name))
 employee=frappe.copy_doc(frappe.get_doc('Employee',base.employee));employee.name=employee_name;employee.docstatus=0
 employee.employee_name='DEV Concurrent Night';employee.user_id=None;employee.company_email=None;employee.personal_email=None
 employee.status='Active';employee.default_shift=shift.name;employee.db_insert();owned.append((employee.doctype,employee.name))
 source_ssa=frappe.get_all('Salary Structure Assignment',filters={'employee':base.employee,'docstatus':1},pluck='name',order_by='from_date desc',limit=1)[0]
 assignment=frappe.copy_doc(frappe.get_doc('Salary Structure Assignment',source_ssa));assignment.name=prefix+'-SSA'
 assignment.employee=employee.name;assignment.docstatus=1;assignment.from_date='2026-01-01';assignment.base=19064;assignment.salary_per_hour=100
 assignment.db_insert();owned.append((assignment.doctype,assignment.name))
 policy=frappe.get_doc({'doctype':'Overtime Pay Policy','title':prefix,'company':employee.company,
  'valid_from':'2026-09-01','valid_until':'2026-09-30','approval_reference':'DEV concurrency fixture only, not an actual approved rule',
  'weekly_threshold':68,'regular_percent':35,'extraordinary_percent':100,'night_percent':15,'weekly_rest_percent':100,
  'night_basis':'Clock overlap','premium_combination':'Additive on base hour','auto_ordinary_night':1})
 policy.insert(ignore_permissions=True);policy.flags.ignore_permissions=True;policy.submit();owned.append((policy.doctype,policy.name))
 for stamp,kind in [('2026-09-14 18:00:00','IN'),('2026-09-14 23:00:00','OUT')]:
  punch=frappe.get_doc({'doctype':'Employee Checkin','employee':employee.name,'time':stamp,'log_type':kind})
  punch.insert(ignore_permissions=True);owned.append((punch.doctype,punch.name))
 call=frappe.copy_doc(frappe.get_doc('Overtime Work Call','CONV-HE-2026-00004-1'));call.name=prefix+'-CALL';call.docstatus=1
 call.company=employee.company;call.status='Authorized';call.authorization_count=1;call.planned_settlement='Cash'
 call.automation_mode='Verified Checkins';call.automatic_settlement_enabled=0;call.evidence_reconciliation_enabled=1;call.evidence_auto_settle=1
 call.db_insert();owned.append((call.doctype,call.name))
 auth=frappe.copy_doc(base);auth.name=prefix+'-AUTH';auth.employee=employee.name;auth.employee_name=employee.employee_name
 auth.shift_type=shift.name;auth.docstatus=1;auth.status='Approved';auth.overtime_work_call=call.name;auth.work_date='2026-09-14'
 auth.authorization_start='2026-09-14 22:00:00';auth.authorization_end='2026-09-14 23:00:00';auth.maximum_hours=1
 auth.planned_settlement='Cash';auth.auto_enrolled=0;auth.evidence_enrolled=1;auth.evidence_auto_settle=1;auth.evidence_status='Pending'
 auth.evidence_snapshot=None;auth.evidence_last_hash=None;auth.evidence_settlement_ready=0;auth.reconciled_on=None;auth.reconciliation_source=None
 auth.verified_hours=0;auth.reconciliation_status='Scheduled';auth.settlement_status='Pending';auth.auto_payroll_date='2026-09-14'
 auth.db_insert();owned.append((auth.doctype,auth.name))
 frappe.db.commit()
 procs=[subprocess.Popen([sys.executable,__file__,auth.name,barrier],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(2)]
 deadline=time.monotonic()+20
 while len(list(Path('/tmp').glob(Path(barrier).name+'.*')))<2:
  assert time.monotonic()<deadline,'workers failed to reach barrier'
  if any(p.poll() is not None for p in procs):
   raise AssertionError([(p.returncode,p.communicate()) for p in procs if p.poll() is not None])
  time.sleep(.02)
 Path(barrier).touch()
 results=[]
 for p in procs:
  out,err=p.communicate(timeout=30);assert p.returncode==0,(out,err)
  results.append(json.loads(out.strip()))
 frappe.db.rollback()
 assert results==[{'status':'Frozen'},{'status':'Frozen'}],results
 auth.reload();frozen=frappe.parse_json(auth.evidence_snapshot)
 nights=frappe.get_all(night.DT,filters={'employee':employee.name,'docstatus':1},fields=['name','settlement_amount'])
 assert len(nights)==1 and nights[0].settlement_amount==15,nights
 assert frozen['ordinary_night_settlement']['name']==nights[0].name and auth.settlement_amount==150
 salaries=frappe.get_all('Additional Salary',filters={'employee':employee.name,'docstatus':1},fields=['ref_doctype','ref_docname','amount'])
 assert len(salaries)==3 and sum(float(r.amount) for r in salaries)==165,salaries
 assert sum(r.ref_doctype==night.DT for r in salaries)==1
 assert sum(r.ref_doctype=='Overtime Authorization' for r in salaries)==2
 print('NIGHT_RACE_ACCEPTANCE: two independent MariaDB workers with old snapshots, one night claim, one OT settlement, three earnings totaling synthetic165')
finally:
 for p in procs:
  if p.poll() is None:p.kill();p.wait()
 for path in Path('/tmp').glob(Path(barrier).name+'*'):path.unlink()
 frappe.db.rollback()
 for dt in ['Additional Salary','Ordinary Night Settlement','Overtime Reconciliation Run']:
  owned.extend((dt,n) for n in frappe.get_all(dt,filters={'employee':employee_name},pluck='name'))
 for dt,name in reversed(owned):
  for field in frappe.get_meta(dt).get_table_fields():
   frappe.db.delete(field.options,{'parent':name,'parenttype':dt})
  for audit in ['Comment','Version','DocShare']:
   filters=({'ref_doctype':dt,'docname':name} if audit=='Version' else
            {'share_doctype':dt,'share_name':name} if audit=='DocShare' else
            {'reference_doctype':dt,'reference_name':name})
   frappe.db.delete(audit,filters)
  frappe.db.delete(dt,{'name':name})
 frappe.db.commit()
 after={d:frappe.db.count(d) for d in types}
 assert baseline==after,(baseline,after)
 assert settings_before==frappe.db.get_singles_dict('DGII Payroll Settings')
 print('NIGHT_RACE_CLEANUP_COUNTS_SETTINGS_UNCHANGED',json.dumps(after))
 frappe.db.rollback();frappe.destroy()
