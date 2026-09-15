import frappe
from frappe import _
from frappe.model.document import Document

from powerpro.retainers.service import (
    AGREEMENT, batch_period, generate_invoices, refresh_batch,
)


class SupplierRetainerBatch(Document):
    def validate(self):
        if self.docstatus != 2:
            previous = self.get_doc_before_save()
            prior_links = {row.name: row.purchase_invoice for row in (previous.details if previous else [])}
            for row in self.details:
                if row.purchase_invoice and row.purchase_invoice != prior_links.get(row.name):
                    frappe.throw(_("Invoice links are assigned by the system."))
            if not previous or previous.docstatus == 0:
                refresh_batch(self)

    @frappe.whitelist()
    def load_agreements(self):
        self.check_permission("write")
        if self.docstatus != 0:
            frappe.throw(_("Agreements can only be loaded into a draft batch."))
        start, end = batch_period(self)
        filters = {
            "docstatus": 1, "company": self.company, "currency": self.currency,
            "frequency": self.frequency, "start_date": ["<=", start],
        }
        if self.supplier:
            filters["supplier"] = self.supplier
        candidates = frappe.get_list(
            AGREEMENT, filters=filters, fields=["name", "end_date"],
            order_by="supplier asc, name asc", limit_page_length=0,
        )
        from frappe.utils import getdate
        self.set("details", [])
        for agreement in candidates:
            if not agreement.end_date or getdate(agreement.end_date) >= end:
                self.append("details", {"agreement": agreement.name})
        self.save()
        return {"count": len(self.details)}

    def before_submit(self):
        generate_invoices(self)

    def before_update_after_submit(self):
        frappe.throw(_("Submitted retainer batches cannot be edited."))

    def before_cancel(self):
        for row in self.details:
            if row.purchase_invoice and frappe.db.get_value("Purchase Invoice", row.purchase_invoice, "docstatus") != 2:
                frappe.throw(_("Cancel purchase invoice {0} before cancelling this batch.").format(row.purchase_invoice))
        self.ignore_linked_doctypes = ("Supplier Retainer Claim", "Purchase Invoice")

    def on_trash(self):
        if any(row.purchase_invoice for row in self.details) or frappe.db.exists("Supplier Retainer Claim", {"batch": self.name}):
            frappe.throw(_("A batch with generated invoices cannot be deleted."))
