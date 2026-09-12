"""Explicit employee/date enrollment for independent ordinary night processing."""
from datetime import timedelta
import frappe
from frappe import _
from frappe.utils import getdate,now_datetime,cint
from frappe.model.document import Document
from powerpro.controllers import ordinary_night as night


class OrdinaryNightAutomation(Document):
    def validate(self):
        if self.docstatus==2:return
        night.check_role()
        employee=frappe.get_doc('Employee',self.employee);employee.check_permission('read')
        self.company=employee.company
        start,end=getdate(self.from_date),getdate(self.to_date)
        if not self.from_date or not self.to_date or not 0<=(end-start).days<31:
            frappe.throw(_('Programe un período de uno a 31 días.'))
        if not self.settlement_payroll_date or getdate(self.settlement_payroll_date)<end:
            frappe.throw(_('La fecha de nómina debe cubrir todo el período programado.'))
        if not (self.reference or '').strip():frappe.throw(_('Documente la referencia de esta programación.'))
        self.validate_policy()
        if self.docstatus==0:
            self.approved_by=None;self.approved_on=None
            self.reset_days()

    def reset_days(self):
        self.set('days',[])
        start,end=getdate(self.from_date),getdate(self.to_date)
        for offset in range((end-start).days+1):self.append('days',{'work_date':start+timedelta(days=offset),'status':'Pending'})

    def validate_policy(self):
        policy=frappe.get_doc('Overtime Pay Policy',self.policy);policy.check_permission('read')
        if (policy.docstatus!=1 or policy.company!=self.company or not cint(policy.auto_ordinary_night)
                or getdate(policy.valid_from)>getdate(self.from_date) or getdate(policy.valid_until)<getdate(self.to_date)):
            frappe.throw(_('Seleccione una política aprobada con nocturnidad automática que cubra este período y empresa.'))

    def before_submit(self):
        frappe.db.get_value('Employee',self.employee,'name',for_update=True)
        others=frappe.get_all(self.doctype,filters=[['employee','=',self.employee],['docstatus','=',1],
            ['from_date','<=',self.to_date],['to_date','>=',self.from_date]],pluck='name',limit=1)
        if others:frappe.throw(_('Ya existe una programación para este empleado y período: {0}.').format(others[0]))
        self.reset_days()
        self.approved_by=frappe.session.user;self.approved_on=now_datetime()

    def before_update_after_submit(self):
        night.check_role()
        if cint(self.enabled):self.validate_policy()
        before=self.get_doc_before_save()
        fields=['name','idx','work_date','status','night_hours','amount','settlement','checked_on','summary','input_hash','issues']
        values=lambda rows:frappe.as_json([{key:row.get(key) for key in fields} for row in rows])
        if values(self.days)!=values(before.days):
            frappe.throw(_('El seguimiento diario se actualiza exclusivamente desde el servicio.'))
        if any(self.get(k)!=before.get(k) for k in ['employee','company','from_date','to_date','settlement_payroll_date','policy','reference','approved_by','approved_on']):
            frappe.throw(_('La programación aprobada es inmutable; únicamente puede pausarse o reanudarse.'))

    def before_cancel(self):
        night.check_role()
        # A paused/cancelled enrollment does not reverse the underlying earnings.
        frappe.db.get_value('Employee',self.employee,'name',for_update=True)
