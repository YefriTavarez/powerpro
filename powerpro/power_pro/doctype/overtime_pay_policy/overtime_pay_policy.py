import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime
from powerpro.payroll_rules.overtime_pay_policy import validate_policy
from powerpro.controllers.overtime import _reconciliation_rows


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
        others=_reconciliation_rows('Overtime Pay Policy',for_update=True,
            filters=[['company','=',self.company],['docstatus','=',1],['name','!=',self.name],
                     ['valid_from','<=',self.valid_until],['valid_until','>=',self.valid_from]],pluck='name',limit=1)
        if others:frappe.throw(_('Ya existe una política aprobada que se superpone con esta vigencia.'))
        self.approved_by=frappe.session.user;self.approved_on=now_datetime()

    def on_update_after_submit(self):
        frappe.throw(_('Las políticas aprobadas son inmutables; cree una nueva versión con su vigencia.'))
