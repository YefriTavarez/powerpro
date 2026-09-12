from datetime import timedelta
import hashlib
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate,now_datetime
from powerpro.controllers.overtime import _reconciliation_rows
from powerpro.controllers.overtime_pay_policy import get_effective_policy
from powerpro.controllers.overtime_rest import require_managed,validate_election
from powerpro.controllers.overtime_source import get_source,claim


class OvertimeSettlementElection(Document):
    def validate(self):
        if self.docstatus==2:return
        auth=get_source(self);auth.check_permission('read')
        policy=get_effective_policy(auth)
        try:self.update(validate_election(self,auth,policy))
        except ValueError as exc:frappe.throw(str(exc))
        if self.docstatus==0:
            self.active_authorization=None;self.active_weekly_rest=None
            self.approved_by=None;self.approved_on=None;self.status='Draft'
            self.leave_application=None;self.actual_start=None;self.actual_end=None
            self.enjoyment_reference=None;self.confirmed_by=None;self.confirmed_on=None

    def before_submit(self):
        require_managed('submit',self.name)
        auth=get_source(self,for_update=True)
        self.previous_method=auth.planned_settlement
        if _reconciliation_rows(self.doctype,for_update=True,filters={'active_authorization':claim(auth)},pluck='name',limit=1):
            frappe.throw(_('Ya hay una elección activa para esta autorización.'))
        self.active_authorization=claim(auth)
        if self.weekly_rest:
            date=getdate(auth.work_date);week=str(date-timedelta(days=date.weekday()))
            self.rest_week=week
            others=_reconciliation_rows(self.doctype,for_update=True,
                filters={'employee':self.employee,'rest_week':week,'docstatus':1,'active_authorization':['is','set']},fields=['choice'])
            if others and (self.choice=='Compensatory Rest' or any(r.choice=='Compensatory Rest' for r in others)):
                frappe.throw(_('El descanso semanal ya tiene una elección incompatible o un crédito; consolide la obligación antes de liquidar.'))
            if self.choice=='Compensatory Rest':self.active_weekly_rest=hashlib.sha256((self.employee+'|'+week).encode()).hexdigest()
        if self.choice=='Compensatory Rest':
            overlaps=_reconciliation_rows(self.doctype,for_update=True,
                filters=[['employee','=',self.employee],['docstatus','=',1],['active_authorization','is','set'],
                         ['choice','=','Compensatory Rest'],['planned_start','<',self.planned_end],['planned_end','>',self.planned_start]],pluck='name',limit=1)
            if overlaps:frappe.throw(_('El mismo intervalo de descanso no puede cumplir dos obligaciones.'))
        self.approved_by=frappe.session.user;self.approved_on=now_datetime();self.status='Approved'

    def before_cancel(self):require_managed('cancel',self.name)

    def on_cancel(self):
        self.db_set({'status':'Cancelled','active_authorization':None,'active_weekly_rest':None})

    def on_update_after_submit(self):
        frappe.throw(_('Utilice las acciones auditadas para programar y confirmar el descanso.'))
