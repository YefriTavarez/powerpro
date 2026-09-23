"""Evidence/earnings services and an employee mutex unavailable in safe_exec."""
from powerpro.controllers import ordinary_night as night
from powerpro.controllers.hr_custom.capabilities import HRScriptDocument
from powerpro.controllers.overtime_cash_settlement import (
    _create_additional_salaries, before_cancel_adjustment, cancel_cash_settlement,
)


class OrdinaryNightSettlement(HRScriptDocument):
    def check_if_latest(self):
        employees = night.lock_employees_before_save(self)
        super().check_if_latest()
        night.check_locked_employee(self, employees)

    def build_night_preview(self):
        return night.build_preview(self)

    def validate_fresh_evidence(self):
        return night.validate_fresh(self)

    def create_night_earnings(self, settlement):
        return _create_additional_salaries(self, settlement)

    def check_earnings_cancellable(self):
        return before_cancel_adjustment(self)

    def cancel_night_earnings(self):
        return cancel_cash_settlement(self)
