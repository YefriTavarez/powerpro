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
 'Working Time Review','Working Time Incident','Working Time Evidence Reference','Version','Error Log',
 'Overtime Work Call','Overtime Evidence Watch','Overtime Authorization','Overtime Reconciliation Run','Ordinary Night Settlement','Additional Salary','Salary Slip']
before={d:frappe.db.count(d) for d in counts}
settings_before={d:frappe.db.get_singles_dict(d) for d in ['DGII Payroll Settings','Payroll Settings']}
commit,enqueue,sendmail=frappe.db.commit,frappe.enqueue,frappe.sendmail

def forbidden(*args,**kwargs):raise AssertionError('Commit or outbound effect forbidden')
frappe.db.commit=forbidden;frappe.enqueue=forbidden;frappe.sendmail=forbidden
prefix='CANCELLED-HISTORY-DEV-'+uuid.uuid4().hex[:8]
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
 from powerpro.controllers import overtime_history as history,overtime_evidence_monitor as monitor
 frappe.db.set_single_value('DGII Payroll Settings',{'enable_manual_overtime_verification':1,'enable_overtime_evidence_monitor':1})
 for day in ['2026-09-07','2026-09-08']:
  for clock,kind in [('08:00:00','IN'),('12:00:00','OUT'),('13:00:00','IN')]:punch(day,clock,kind)
 first_exit=punch('2026-09-07','20:00:00','OUT');punch('2026-09-08','20:00:00','OUT')
 first=draft('2026-09-07');first.submit();first.reload()
 second=draft('2026-09-08');second.submit();second.reload()
 first.flags.ignore_permissions=True;first.cancel();first.reload()
 protected={k:first.get(k) for k in ['docstatus','status','modified','verified_hours','settlement_amount','settlement_status','evidence_snapshot','reconciliation_source']}
 assert monitor.check_source(DT,first.name)['status']=='Current'
 first_exit.time='2026-09-07 19:00:00';first_exit.save(ignore_permissions=True)
 assert monitor.check_source(DT,first.name)['status']=='Needs Review'
 def preview(doc,reason='DEV physical correction',declaration=None):
  return history.preview_review(doc.name,reason,manual_declaration=declaration,source_type=DT)
 def apply(doc,p,reason='DEV physical correction',declaration=None):
  return history.apply_review(doc.name,reason,p['token'],manual_declaration=declaration,source_type=DT)
 p=preview(first);assert p['historical_only'] and p['worked_hours_before']==11 and p['worked_hours_after']==10
 try:apply(first,p)
 except frappe.ValidationError as exc:assert second.name in str(exc)
 else:raise AssertionError('History correction bypassed settled dependency')
 second.flags.ignore_permissions=True;second.cancel();second.reload()
 p=preview(first)
 first_exit.time='2026-09-07 18:30:00';first_exit.save(ignore_permissions=True)
 try:apply(first,p)
 except frappe.ValidationError:pass
 else:raise AssertionError('Stale historical preview accepted')
 first_exit.time='2026-09-07 19:00:00';first_exit.save(ignore_permissions=True)
 p=preview(first);money=frappe.db.count('Additional Salary');punch_count=frappe.db.count('Employee Checkin')
 result=apply(first,p);assert result['history_sequence']==1
 assert apply(first,p)['idempotent']
 first.reload();assert protected=={k:first.get(k) for k in protected}
 assert frappe.db.count('Additional Salary')==money and frappe.db.count('Employee Checkin')==punch_count
 assert monitor.check_source(DT,first.name)['status']=='Current'
 # A cancelled later source does not become stale just because its original
 # weekly rate basis changed; only physical evidence remains relevant there.
 assert monitor.check_source(DT,second.name)['status']=='Current'
 third=draft('2026-09-08');projection=retro.reconcile(third)
 assert projection['_evidence']['calculation']['segments'][0]['actual_weekly_hours_before']==19
 third.submit();third.reload();third.flags.ignore_permissions=True;third.cancel()
 first_exit.skip_auto_attendance=1;first_exit.save(ignore_permissions=True)
 try:preview(first)
 except frappe.ValidationError:pass
 else:raise AssertionError('Missing exit was accepted as physical proof')
 declaration={'full_session':True,'reference':'DEV historical signed record',
  'intervals':[{'start':'2026-09-07 08:00:00','end':'2026-09-07 12:00:00'},
               {'start':'2026-09-07 13:00:00','end':'2026-09-07 19:30:00'}]}
 p=preview(first,'DEV declared history',declaration)
 result=apply(first,p,'DEV declared history',declaration);assert result['history_sequence']==2
 from powerpro.controllers import working_time_controls as controls,working_time_incidents as cases,working_time_reviews as reviews
 diagnostic=controls.preview(DT,first.name)
 assert diagnostic['historical_review']['accepted'] and diagnostic['current_evidence_state']=='Verified'
 assert diagnostic['supporting_evidence']['session']['worked_intervals']==history.compare(first)['current']['worked_intervals']
 first.reload();assert protected=={k:first.get(k) for k in protected}
 fourth=draft('2026-09-08');projection=retro.reconcile(fourth)
 assert projection['_evidence']['calculation']['segments'][0]['actual_weekly_hours_before']==19.5
 # Confirmed ordinary work with no OT is still actual weekly work. It is not
 # a fictional absent day or a revived payment on the cancelled source.
 first_exit.skip_auto_attendance=0;first_exit.time='2026-09-07 18:00:00';first_exit.save(ignore_permissions=True)
 p=preview(first);assert p['after']['verified_hours']==0 and p['worked_hours_after']==9
 assert apply(first,p)['history_sequence']==3
 projection=retro.reconcile(fourth)
 assert projection['_evidence']['calculation']['segments'][0]['actual_weekly_hours_before']==18
 first.reload();assert protected=={k:first.get(k) for k in protected}
 assert frappe.db.count('Employee Checkin')==punch_count
 # A Sunday extension contributes to Monday's week. A settled Monday source
 # must block editing the Sunday evidence even though work_date is prior week.
 employee=frappe.copy_doc(employee);employee.name=prefix+'-CROSSWEEK';employee.docstatus=0;employee.db_insert()
 assignment=frappe.copy_doc(assignment);assignment.name=prefix+'-CROSSWEEK-SSA';assignment.docstatus=1;assignment.employee=employee.name;assignment.db_insert()
 punch('2026-09-06','22:00:00','IN');overnight_exit=punch('2026-09-07','02:00:00','OUT')
 for clock,kind in [('08:00:00','IN'),('12:00:00','OUT'),('13:00:00','IN'),('20:00:00','OUT')]:punch('2026-09-07',clock,kind)
 sunday=frappe.get_doc({'doctype':DT,'employee':employee.name,'work_date':'2026-09-06',
  'authorization_start':'2026-09-06 22:00:00','authorization_end':'2026-09-07 02:00:00','maximum_hours':4,
  'reason':'DEV cross-week','exception_justification':'DEV historical cross-week exception','planned_settlement':'Cash',
  'settlement_payroll_date':'2026-09-15','reconciliation_engine':retro.ENGINE})
 sunday.insert(ignore_permissions=True);sunday.flags.ignore_permissions=True;sunday.submit();sunday.cancel();sunday.reload()
 monday=draft('2026-09-07');monday.submit();monday.reload()
 overnight_exit.time='2026-09-07 01:00:00';overnight_exit.save(ignore_permissions=True)
 p=preview(sunday);assert any(r['name']==monday.name and r['blocks_reversal'] for r in p['dependencies'])
 try:apply(sunday,p)
 except frappe.ValidationError as exc:assert monday.name in str(exc)
 else:raise AssertionError('Sunday correction bypassed Monday payroll dependency')
 monday.flags.ignore_permissions=True;monday.cancel()
 # The same audited route serves a natively created/cancelled authorization.
 employee=frappe.copy_doc(employee);employee.name=prefix+'-AUTH';employee.docstatus=0;employee.db_insert()
 assignment=frappe.copy_doc(assignment);assignment.name=prefix+'-AUTH-SSA';assignment.docstatus=1;assignment.employee=employee.name;assignment.db_insert()
 punch('2026-09-14','08:00:00','IN');auth_exit=punch('2026-09-14','20:00:00','OUT')
 call=frappe.copy_doc(frappe.get_doc('Overtime Work Call','CONV-HE-2026-00004-1'));call.name=None;call.docstatus=0
 call.company=employee.company;call.from_date='2026-09-14';call.to_date='2026-09-14';call.planned_settlement='Cash'
 call.automation_mode='Verified Checkins';call.evidence_auto_settle=0
 call.set('employees',[]);call.append('employees',{'employee':employee.name})
 call.set('dates',[]);call.append('dates',{'work_date':'2026-09-14','start_time':'18:00:00','end_time':'20:00:00','requested_hours':2})
 call.insert(ignore_permissions=True);call.flags.ignore_permissions=True;call.submit()
 auth_name=frappe.db.get_value('Overtime Authorization',{'overtime_work_call':call.name},'name')
 with patch.object(evidence,'now_datetime',return_value=get_datetime('2026-09-14 21:00:00')):
  evidence.process_authorization(auth_name)
  call.reload();call.flags.ignore_permissions=True;call.cancel()
  auth=frappe.get_doc('Overtime Authorization',auth_name)
  original=auth.evidence_snapshot
  diagnostic=controls.preview(auth.doctype,auth.name)
  assert diagnostic['historical_only'] and diagnostic['historical_review']['accepted'] and not diagnostic['historical_review']['revision']
  rows=cases.record(auth.doctype,auth.name,{},'Administrator',diagnostic['input_hash'])
  daily=frappe.get_doc(cases.DT,next(r['name'] for r in rows if frappe.db.get_value(cases.DT,r['name'],'control_code')=='daily_work'))
  assert daily.status=='Open' and daily.evaluation_status=='Review'
  cases.resolve(daily.name,daily.evidence_hash,'Documented Exception','DEV accepted long historical session','DEV exception')
  auth_exit.time='2026-09-14 19:00:00';auth_exit.save(ignore_permissions=True)
  cases.recheck(daily.name);daily.reload();assert daily.evaluation_status=='Historical review required' and daily.status=='Open'
  p=history.preview_review(auth_name,'DEV cancelled authorization',source_type='Overtime Authorization')
  result=history.apply_review(auth_name,'DEV cancelled authorization',p['token'],source_type='Overtime Authorization')
  assert result['history_sequence']==1 and history.compare(auth)['matches']
  protected=frappe.get_doc(auth.doctype,auth.name).as_dict();money=frappe.db.count('Additional Salary')
  frappe.db.set_single_value('DGII Payroll Settings','enable_working_time_incident_monitor',1)
  assert reviews.process_review(daily.working_time_review)['status']=='Checked'
  daily.reload();assert daily.evaluation_status=='Review' and daily.status=='Open' and daily.resolution_reference=='DEV exception'
  assert any(r.document_type=='Overtime Reconciliation Run' and r.document_name==result['audit'] for r in daily.evidence_references)
  cases.resolve(daily.name,daily.evidence_hash,'Documented Exception','DEV accepted revised historical session','DEV revision')
  assert not cases.recheck(daily.name)['changed']
  assert frappe.get_doc(auth.doctype,auth.name).as_dict()==protected and frappe.db.count('Additional Salary')==money
  auth.reload();assert auth.docstatus==2 and auth.evidence_snapshot==original and auth.verified_hours==2
 print('CANCELLED_HISTORY: append-only physical correction, immutable cancelled finance/source, stale-token and settled-dependent guards, manual evidence and zero-OT ordinary work, actual weekly19/19.5/18, Sunday->Monday impact passed')
finally:
 frappe.db.rollback();frappe.db.commit=commit;frappe.enqueue=enqueue;frappe.sendmail=sendmail
 after={d:frappe.db.count(d) for d in counts}
 assert before==after,(before,after)
 for dt,values in settings_before.items():assert values==frappe.db.get_singles_dict(dt),dt
 print('CANCELLED_HISTORY_ROLLBACK',json.dumps(after))
 frappe.destroy()
