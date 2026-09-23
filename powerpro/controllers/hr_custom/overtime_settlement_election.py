"""Shared evidence evaluation and trusted action identity require app imports."""
import frappe
from powerpro.controllers.hr_custom.capabilities import HRScriptDocument


class OvertimeSettlementElection(HRScriptDocument):
    def is_managed_action(self, action):
        return frappe.flags.get('overtime_election_action') == (action, self.name)

    def evaluate_election(self, auth):
        from powerpro.controllers.overtime_pay_policy import get_effective_policy
        from powerpro.controllers.overtime_rest import validate_election
        return validate_election(self, auth, get_effective_policy(auth))
