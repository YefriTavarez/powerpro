"""Only pre-save locking and the worker-to-script adapter remain native."""
from powerpro.controllers import ordinary_night as night
from powerpro.controllers.hr_custom.capabilities import HRScriptDocument, automation_policy_for_worker


class OrdinaryNightAutomation(HRScriptDocument):
    def check_if_latest(self):
        employees = night.lock_employees_before_save(self)
        super().check_if_latest()
        night.check_locked_employee(self, employees)

    def validate_policy(self):
        # Called by both the worker and submitted-document Server Script.
        return automation_policy_for_worker(self)
