"""Keep HRMS leave submit/cancel locks consistent with overtime balance checks."""
from hrms.hr.doctype.leave_application.leave_application import LeaveApplication
from powerpro.controllers.overtime_document_locks import lock_employees_before_save, check_locked_employee


class OvertimeLeaveApplication(LeaveApplication):
    def check_if_latest(self):
        if self.docstatus == 0:
            return super().check_if_latest()
        # The existing submit/cancel hooks already lock Employee, but native
        # check_if_latest would lock Leave Application before those hooks run.
        employees = lock_employees_before_save(self)
        super().check_if_latest()
        check_locked_employee(self, employees)
