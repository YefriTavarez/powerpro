import hashlib
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate, now_datetime
from powerpro.controllers import ordinary_night as night
from powerpro.controllers.checkin_overtime import _json
from powerpro.controllers.overtime import _reconciliation_rows
from powerpro.controllers.overtime_cash_settlement import _create_additional_salaries, before_cancel_adjustment, cancel_cash_settlement


class OrdinaryNightSettlement(Document):
    def check_if_latest(self):
        employees = night.lock_employees_before_save(self)
        super().check_if_latest()
        night.check_locked_employee(self, employees)

    def validate(self):
        if self.docstatus==2:return
        if self.docstatus==0:
            night.check_role()
            result=night.build_preview(self)
            self.company=result['input']['company'];self.shift_type=result['input']['shift']['name'];self.policy=result['input']['policy']['name']
            self.evidence_snapshot=_json(result);self.evidence_status=result['state'];self.issues=_json(result['issues'])
            self.night_hours=result['ordinary_hours'];self.hourly_rate=result['hourly_rate'];self.night_percent=result['night_percent']
            self.settlement_amount=result['amount'];self.currency=result['currency']
            self.status='Draft';self.settlement_status='Pending';self.active_claim=None;self.additional_salary=None
            self.approved_by=None;self.approved_on=None
        if not self.settlement_payroll_date or getdate(self.settlement_payroll_date)<getdate(self.work_date):
            frappe.throw(_('La fecha de nómina no puede ser anterior al trabajo.'))

    def before_submit(self):
        night.check_role()
        settings=frappe.get_single('DGII Payroll Settings')
        if not cint(settings.get('enable_checkin_overtime_reconciliation')) or not settings.checkin_overtime_effective_from or getdate(self.work_date)<getdate(settings.checkin_overtime_effective_from):
            frappe.throw(_('La conciliación por marcaciones debe estar habilitada y cubrir esta fecha.'))
        frappe.db.get_value('Employee',self.employee,'name',for_update=True)
        current=night.validate_fresh(self)
        if current['input'].get('certified_session') and not cint(settings.get('enable_manual_overtime_verification')):
            frappe.throw(_('La verificación manual debe estar habilitada para liquidar esta declaración.'))
        self.evidence_snapshot=_json(current);self.evidence_status=current['state'];self.issues=_json(current['issues'])
        self.shift_type=current['input']['shift']['name'];self.policy=current['input']['policy']['name']
        # Ignore any client-supplied derived fields, even on a direct submit request.
        self.night_hours=current['ordinary_hours'];self.hourly_rate=current['hourly_rate'];self.night_percent=current['night_percent']
        self.settlement_amount=current['amount'];self.currency=current['currency'];self.company=current['input']['company']
        self.active_claim=hashlib.sha256(f'{self.employee}|{getdate(self.work_date)}'.encode()).hexdigest()
        others=_reconciliation_rows(self.doctype,for_update=True,filters={'active_claim':self.active_claim,'docstatus':1},pluck='name',limit=1)
        if others:frappe.throw(_('Ya existe una liquidación nocturna ordinaria para esta jornada.'))
        self.status='Approved';self.approved_by=frappe.session.user;self.approved_on=now_datetime()

    def on_submit(self):
        settlement={'currency':self.currency,'payroll_date':str(self.settlement_payroll_date),
            'lines':[{'component':'Horas Nocturnas','amount':self.settlement_amount}]}
        names=_create_additional_salaries(self,settlement)
        self.db_set({'additional_salary':names[0],'settlement_status':'Created'})

    def before_cancel(self):
        night.check_role()
        frappe.db.get_value('Employee',self.employee,'name',for_update=True)
        before_cancel_adjustment(self)
        for source_type in ['Overtime Authorization','Retroactive Overtime Adjustment']:
            refs=_reconciliation_rows(source_type,for_update=True,filters={'employee':self.employee,'work_date':self.work_date,'docstatus':1,
                'settlement_status':['in',list(night.FINAL)]},fields=['name','evidence_snapshot'])
            for ref in refs:
                snapshot=frappe.parse_json(ref.evidence_snapshot or '{}')
                if (snapshot.get('ordinary_night_settlement') or {}).get('name')==self.name:
                    frappe.throw(_('Revierta primero las horas extra vinculadas a esta jornada: {0} {1}.').format(source_type,ref.name))

    def on_cancel(self):
        cancel_cash_settlement(self)
        self.db_set('active_claim',None)

    def on_update_after_submit(self):
        frappe.throw(_('La evidencia enviada es inmutable; cancele y cree una liquidación corregida.'))
