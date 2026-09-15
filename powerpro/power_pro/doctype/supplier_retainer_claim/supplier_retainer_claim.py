import frappe
from frappe import _
from frappe.model.document import Document

from powerpro.retainers.periods import claim_key


class SupplierRetainerClaim(Document):
    def autoname(self):
        self.name = claim_key(self.agreement_identity, self.period_start, self.period_end)

    def validate(self):
        if not self.flags.retainer_service:
            frappe.throw(_("Billing claims are maintained by the retainer workflow."), frappe.PermissionError)

    def on_trash(self):
        frappe.throw(_("Billing claims cannot be deleted."))
