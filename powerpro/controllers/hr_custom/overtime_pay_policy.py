import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime
from powerpro.payroll_rules.overtime_pay_policy import validate_policy
from powerpro.controllers.overtime import _reconciliation_rows
from powerpro.controllers.overtime_pay_policy import active_revisions,policy_rows
from frappe.utils import getdate


class OvertimePayPolicy(Document):
    def validate(self):
        try:validate_policy(self.as_dict())
        except ValueError as exc:frappe.throw(str(exc))
        if self.docstatus==0:
            self.approved_by=None;self.approved_on=None

    def before_submit(self):
        if not {'System Manager','HR Manager'}.intersection(frappe.get_roles()):
            frappe.throw(_('Su rol no permite aprobar políticas de horas extra.'),frappe.PermissionError)
        frappe.db.get_value('Company',self.company,'name',for_update=True)
        others=active_revisions(policy_rows(self.company,self.valid_from,self.valid_until,for_update=True))
        others=[r for r in others if r.name!=self.name]
        if self.get('supersedes'):
            if (len(others)!=1 or others[0].name!=self.supersedes
                or getdate(others[0].valid_from)!=getdate(self.valid_from)
                or getdate(others[0].valid_until)!=getdate(self.valid_until)):
                frappe.throw(_('La revisión debe partir de la versión vigente y conservar su empresa y fechas. Recargue las reglas.'))
        elif others:
            frappe.throw(_('Ya existe una política aprobada que se superpone con esta vigencia.'))
        self.approved_by=frappe.session.user;self.approved_on=now_datetime()

    def on_update_after_submit(self):
        frappe.throw(_('Las políticas aprobadas son inmutables; cree una nueva versión con su vigencia.'))

    def before_cancel(self):
        frappe.db.get_value('Company',self.company,'name',for_update=True)
        if _reconciliation_rows('Overtime Pay Policy',for_update=True,
                filters={'supersedes':self.name,'docstatus':1},pluck='name',limit=1):
            frappe.throw(_('Esta versión tiene una revisión aprobada. Conserve la cadena de reglas.'))
