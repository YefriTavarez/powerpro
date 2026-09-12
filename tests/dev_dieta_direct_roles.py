"""DEV native creation with existing Finance/HR users and effective scope.

No impersonation credentials or HTTP authentication are manufactured. This
checks native permissions under each existing user's identity, not browser QA.
All newly inserted Dietas and failed attempts are rolled back. Existing scope,
roles, employees and configuration are never changed.
"""
import json,uuid
from datetime import timedelta
import frappe
from frappe.utils import getdate

frappe.init(site='igcaribe.fortabs.com');frappe.connect();frappe.set_user('Administrator')
assert frappe.local.site=='igcaribe.fortabs.com' and frappe.conf.developer_mode
from powerpro.dietas import permissions as access,service
DT=access.REQUEST
counts=[DT,'Lote de Pago de Dietas','Dieta Payout Row','Employee','User','User Permission','Has Role','Journal Entry',
 'GL Entry','Additional Salary','Salary Slip','Version','Comment','Notification Log','Error Log']
before={dt:frappe.db.count(dt) for dt in counts}
settings_before=frappe.get_single('IGC Settings').as_dict()
commit,enqueue,sendmail=frappe.db.commit,frappe.enqueue,frappe.sendmail

def forbidden(*a,**kw):raise AssertionError('Commit or outbound effect forbidden')
frappe.db.commit=forbidden;frappe.enqueue=forbidden;frappe.sendmail=forbidden

def refused(fn,exceptions=(frappe.ValidationError,frappe.PermissionError)):
 point='dieta_refusal_'+uuid.uuid4().hex;frappe.db.savepoint(point)
 try:
  try:fn()
  except exceptions:return
  raise AssertionError('Expected explicit refusal')
 finally:frappe.db.rollback(save_point=point)

try:
 companies={r.company for r in frappe.get_single('IGC Settings').dieta_companies if r.enabled}
 candidates=frappe.get_all('Employee',filters={'status':'Active','company':['in',list(companies)]},
  fields=['name','company','department','user_id'])
 for user,role in [('aalmanzar@igcaribe.com','Gerente Finanzas'),('asantos@equipo.igcaribe.com','Encargado Gestión Humana')]:
  assert frappe.db.get_value('User',user,'enabled') and role in frappe.get_roles(user)
  frappe.set_user(user)
  allowed=[emp for emp in candidates if access.can_create_for_employee(emp,user)]
  assert allowed,(user,'No employee available within actual permissions')
  emp=allowed[0]
  assert frappe.get_list('Employee',filters={'name':emp.name},pluck='name')==[emp.name]
  date=getdate('2026-09-12')
  for offset in range(31):
   date=getdate('2026-09-12')+timedelta(days=offset)
   if not frappe.db.exists(DT,{'employee':emp.name,'work_date':date}):break
  else:raise AssertionError('No free synthetic date in bounded test range')
  cfg=service.settings(emp.company)
  def draft(employee=emp.name):
   return frappe.get_doc(dict(doctype=DT,employee=employee,company=emp.company,work_date=date,
    amount=cfg.default_amount,currency=cfg.currency,notes='DEV rollback-only direct role verification'))
  doc=draft()
  # A create-permitted user still cannot forge approval/payment/audit state.
  doc.update(dict(approval_status='Approved',payment_status='Paid',approved_by=user,paid_by=user,
   initiated_by='Administrator',audit_log='[{"action":"forged"}]'))
  doc.insert()
  assert not doc.authorization and not doc.overtime_work_call and doc.docstatus==0
  assert doc.approval_status=='Pending' and doc.payment_status=='Unpaid'
  assert doc.initiated_by==user and not doc.approved_by and not doc.paid_by
  assert all(r.get('action')!='forged' for r in frappe.parse_json(doc.audit_log))
  saved=frappe.get_doc(DT,doc.name);saved.check_permission('read')
  assert frappe.get_list(DT,filters={'name':doc.name},pluck='name')==[doc.name]
  refused(lambda:draft().insert())
  saved.notes='Attempted unmanaged edit';refused(lambda:saved.save())
  own=next((e for e in candidates if e.user_id==user),None)
  if own:refused(lambda:draft(own.name).insert())
  outside=next((e for e in candidates if e.user_id!=user and not access.in_scope(e,user)),None)
  if outside:refused(lambda:draft(outside.name).insert())
  print('DIETA_ROLE_NATIVE',json.dumps(dict(user=user,role=role,eligible_employees=len(allowed),
   native_employee_lookup=True,created_without_overtime=True,read_and_list=True,
   forged_payment_reset=True,duplicate_refused=True,unmanaged_edit_refused=True,
   self_request_refused=bool(own),out_of_scope_refused=bool(outside),retained=False)),flush=True)
finally:
 frappe.set_user('Administrator');frappe.db.rollback()
 frappe.db.commit=commit;frappe.enqueue=enqueue;frappe.sendmail=sendmail
 after={dt:frappe.db.count(dt) for dt in counts};assert before==after,(before,after)
 assert settings_before==frappe.get_single('IGC Settings').as_dict()
 print('DIETA_DIRECT_ROLES_ROLLBACK',json.dumps(after));frappe.db.rollback();frappe.destroy()
