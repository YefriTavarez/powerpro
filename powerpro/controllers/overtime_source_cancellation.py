"""Native cancellation must acquire the same mutexes as settlement services."""
import frappe
from frappe import _
from powerpro.controllers.overtime_document_locks import lock_employees_before_save, check_locked_employee
from powerpro.power_pro.doctype.overtime_authorization.overtime_authorization import OvertimeAuthorization
from powerpro.power_pro.doctype.retroactive_overtime_adjustment.retroactive_overtime_adjustment import RetroactiveOvertimeAdjustment


class SourceCancellationLocks:
    def check_if_latest(self):
        if self.docstatus != 2:
            return super().check_if_latest()
        calls = set()
        if self.meta.has_field('overtime_work_call'):
            stored = frappe.db.get_value(self.doctype, self.name, 'overtime_work_call')
            calls = {name for name in (stored, self.get('overtime_work_call')) if name}
            for name in sorted(calls):
                frappe.db.get_value('Overtime Work Call', name, 'name', for_update=True)
        employees = lock_employees_before_save(self)
        super().check_if_latest()
        check_locked_employee(self, employees)
        before = self.get_doc_before_save()
        if before and before.get('overtime_work_call') and before.overtime_work_call not in calls:
            frappe.throw(_('La convocatoria de la autorización cambió; recargue antes de cancelar.'))


class LockedOvertimeAuthorization(SourceCancellationLocks, OvertimeAuthorization):
    pass


class LockedRetroactiveOvertimeAdjustment(SourceCancellationLocks, RetroactiveOvertimeAdjustment):
    pass
