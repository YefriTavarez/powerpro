"""Current ledger reads for the shared overtime allocation under MariaDB locks."""
from hrms.hr.doctype.leave_allocation.leave_allocation import LeaveAllocation

class OvertimeLeaveAllocation(LeaveAllocation):
    def get_existing_leave_count(self):
        if not self.get('powerpro_overtime_managed'):
            return super().get_existing_leave_count()
        from powerpro.controllers.overtime import _reconciliation_rows
        from frappe.utils import flt
        rows = _reconciliation_rows('Leave Ledger Entry', for_update=True, filters={
            'transaction_type': 'Leave Allocation', 'transaction_name': self.name,
            'employee': self.employee, 'company': self.company, 'leave_type': self.leave_type,
            'is_carry_forward': 0, 'docstatus': 1}, fields=['leaves'])
        return sum(flt(row.leaves) for row in rows)
