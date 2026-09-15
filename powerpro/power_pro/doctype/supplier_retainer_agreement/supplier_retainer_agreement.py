from decimal import Decimal

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from powerpro.retainers.service import validate_agreement


class SupplierRetainerAgreement(Document):
    def validate(self):
        validate_agreement(self)

    def before_update_after_submit(self):
        previous = self.get_doc_before_save()
        if previous:
            for field in (
                "title", "supplier", "company", "item", "gross_amount", "currency",
                "frequency", "start_date", "end_date", "expense_account",
                "cost_center", "description", "amended_from",
            ):
                old, new = previous.get(field), self.get(field)
                if field in ("start_date", "end_date"):
                    old, new = getdate(old) if old else None, getdate(new) if new else None
                elif field == "gross_amount":
                    old, new = Decimal(str(old or 0)), Decimal(str(new or 0))
                if (old or None) != (new or None):
                    frappe.throw(_("Agreement conditions cannot change after submission. Cancel and amend the agreement."))
        if previous and previous.taxes_and_charges != self.taxes_and_charges:
            if not set(frappe.get_roles()).intersection({"Accounts Manager", "System Manager"}):
                frappe.throw(_("Only Accounts Manager or System Manager may change the tax template after submission."), frappe.PermissionError)
        self.validate()

    def before_cancel(self):
        # Claims and past batches are historical references, not open obligations.
        self.ignore_linked_doctypes = ("Supplier Retainer Claim", "Supplier Retainer Batch", "Purchase Invoice")

    def on_trash(self):
        if (
            frappe.db.exists("Supplier Retainer Claim", {"agreement_identity": self.name})
            or frappe.db.exists("Supplier Retainer Claim", {"agreement": self.name})
            or frappe.db.exists("Supplier Retainer Batch Detail", {"agreement": self.name})
            or frappe.db.exists("Supplier Retainer Agreement", {"amended_from": self.name})
        ):
            frappe.throw(_("An agreement with billing history cannot be deleted."))
