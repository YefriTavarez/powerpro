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
counts=['Shift Assignment','Employee','Shift Type','Employee Checkin','Salary Structure Assignment','Overtime Pay Policy',DT,
 'Working Time Review','Working Time Incident','Working Time Evidence Reference','Version','Error Log',
 'Overtime Work Call','Overtime Evidence Watch','Overtime Authorization','Overtime Reconciliation Run','Ordinary Night Settlement','Additional Salary','Salary Slip']
before={d:frappe.db.count(d) for d in counts}
settings_before={d:frappe.db.get_singles_dict(d) for d in ['DGII Payroll Settings','Payroll Settings']}
commit,enqueue,sendmail=frappe.db.commit,frappe.enqueue,frappe.sendmail

def forbidden(*args,**kwargs):raise AssertionError('Commit or outbound effect forbidden')
frappe.db.commit=forbidden;frappe.enqueue=forbidden;frappe.sendmail=forbidden
prefix='OBSERVATION-WINDOW-DEV-'+uuid.uuid4().hex[:8]
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
 from powerpro.controllers import overtime_history as history,working_time_controls as controls
 frappe.db.set_single_value('DGII Payroll Settings',{'enable_manual_overtime_verification':1,'enable_overtime_evidence_monitor':1})
 # Stored Shift Assignment ensures the historical weekly loader accepts the
 # serialized assignment dictionaries from a real evidence snapshot.
 frappe.get_doc({'doctype':'Shift Assignment','employee':employee.name,'shift_type':shift.name,
  'start_date':'2026-09-01','end_date':'2026-09-30','status':'Active','docstatus':1}).db_insert()
 # Monday was settled before the previous day's late evidence arrived.
 for clock,kind in [('08:00:00','IN'),('12:00:00','OUT'),('13:00:00','IN'),('20:00:00','OUT')]:punch('2026-09-07',clock,kind)
 monday=draft('2026-09-07');monday.submit();monday.reload()
 assert monday.settlement_status=='Created'
 entry=punch('2026-09-06','22:00:00','IN');exit_mark=punch('2026-09-06','23:00:00','OUT')
 first=draft('2026-09-06','22:00:00','23:00:00',1);first.submit();first.reload()
 first.flags.ignore_permissions=True;first.cancel();first.reload();original=first.as_dict()
 def fails(fn):
  try:fn()
  except (frappe.ValidationError,ValueError):return
  raise AssertionError('Expected refusal')
 exit_mark.time='2026-09-07 02:00:00';exit_mark.save(ignore_permissions=True)
 fails(lambda:history.preview_review(first.name,'No expanded window',source_type=DT))
 window={'start':'2026-09-06 08:00:00','end':'2026-09-07 02:00:00'}
 def preview(reason='DEV extended overnight window',declaration=None,window=window):
  return history.preview_review(first.name,reason,source_type=DT,manual_declaration=declaration,observation_window=window)
 def apply(p,reason='DEV extended overnight window',declaration=None,window=window):
  return history.apply_review(first.name,reason,p['token'],source_type=DT,manual_declaration=declaration,observation_window=window)
 p=preview();assert p['worked_hours_before']==1 and p['worked_hours_after']==4 and p['after']['verified_hours']==1
 assert p['unapproved_hours']==3 and p['historical_only'] and not p['settlement_ready']
 assert any(r['name']==monday.name and r['blocks_reversal'] for r in p['dependencies']),(monday.settlement_status,frappe.parse_json(monday.evidence_snapshot).get('settlement_blockers'),p['dependencies'])
 fails(lambda:apply(p))
 monday.flags.ignore_permissions=True;monday.cancel();monday.reload()
 p=preview();exit_mark.time='2026-09-07 01:30:00';exit_mark.save(ignore_permissions=True);fails(lambda:apply(p))
 exit_mark.time='2026-09-07 02:00:00';exit_mark.save(ignore_permissions=True)
 p=preview();money=frappe.db.count('Additional Salary');marks=frappe.db.count('Employee Checkin')
 result=apply(p);assert result['history_sequence']==1 and apply(p)['idempotent']
 current=history.compare(first);assert current['matches'] and len(current['current']['input']['assignments'])==1
 assert current['current']['input']['authorization']['end']=='2026-09-06 23:00:00'
 diagnostic=controls.preview(DT,first.name);assert diagnostic['historical_review']['accepted']
 assert get_datetime(diagnostic['supporting_evidence']['weekly']['cutoff'])==get_datetime(window['end'])
 # Original Sunday authorization ended before this week. Its reviewed Monday
 # carry must nevertheless contribute two hours to the later Monday band.
 replacement=draft('2026-09-07');projection=retro.reconcile(replacement)
 assert projection['_evidence']['calculation']['segments'][0]['actual_weekly_hours_before']==11,projection
 # A later declaration can expand further but cannot truncate the previously
 # accepted observation scope. The original authorization still caps OT at1h.
 exit_mark.skip_auto_attendance=1;exit_mark.save(ignore_permissions=True)
 later={'start':'2026-09-06 08:00:00','end':'2026-09-07 03:00:00'}
 declaration={'full_session':True,'reference':'DEV supervisor overnight record','intervals':[
  {'start':'2026-09-06 22:00:00','end':'2026-09-07 03:00:00'}]}
 p=preview('DEV declared wider window',declaration,later);assert p['worked_hours_after']==5 and p['unapproved_hours']==4
 result=apply(p,'DEV declared wider window',declaration,later);assert result['history_sequence']==2
 assert history.compare(first)['matches']
 fails(lambda:preview('Cannot hide accepted window',declaration,window))
 projection=retro.reconcile(replacement)
 assert projection['_evidence']['calculation']['segments'][0]['actual_weekly_hours_before']==12
 first.reload();assert first.as_dict()==original and frappe.db.count('Additional Salary')==money and frappe.db.count('Employee Checkin')==marks
 # The same API supports a natively enrolled/cancelled Authorization.
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
 with patch.object(evidence,'now_datetime',return_value=get_datetime('2026-09-16 10:00:00')):
  evidence.process_authorization(auth_name)
  live=frappe.get_doc('Overtime Authorization',auth_name)
  fails(lambda:evidence._data(live,observation_window={'start':'2026-09-14 08:00:00','end':'2026-09-15 06:00:00'}))
  call.reload();call.flags.ignore_permissions=True;call.cancel();auth=frappe.get_doc('Overtime Authorization',auth_name);protected=auth.as_dict()
  auth_exit.time='2026-09-15 06:00:00';auth_exit.save(ignore_permissions=True)
  observed={'start':'2026-09-14 08:00:00','end':'2026-09-15 06:00:00'}
  p=history.preview_review(auth_name,'DEV authorization overrun',observation_window=observed)
  assert p['worked_hours_after']==22 and p['after']['verified_hours']==2 and p['unapproved_hours']==10
  history.apply_review(auth_name,'DEV authorization overrun',p['token'],observation_window=observed)
  assert history.compare(auth)['matches']
  auth.reload();assert auth.as_dict()==protected
 print('HISTORICAL_WINDOW: explicit raw/manual expansion, original OT caps/source preserved, Sunday-to-Monday dependent gate and11/12h weekly bands, native Shift Assignment, stale/idempotent/reduction guards and cancelled Authorization passed')
finally:
 frappe.db.rollback();frappe.db.commit=commit;frappe.enqueue=enqueue;frappe.sendmail=sendmail
 after={d:frappe.db.count(d) for d in counts};assert before==after,(before,after)
 for dt,values in settings_before.items():assert values==frappe.db.get_singles_dict(dt),dt
 print('HISTORICAL_WINDOW_ROLLBACK',json.dumps(after));frappe.destroy()
