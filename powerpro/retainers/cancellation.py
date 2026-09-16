"""Undo a batch's unissued drafts through normal document deletion hooks."""
from contextlib import contextmanager
from contextvars import ContextVar
from uuid import uuid4

import frappe
from frappe import _
from frappe.utils import cint, escape_html


_discarding = ContextVar("retainer_draft_discard", default=None)


@contextmanager
def discarding_draft(batch, invoice):
    token = _discarding.set((batch, invoice))
    try:
        yield
    finally:
        _discarding.reset(token)


def may_discard(doc):
    return (
        cint(doc.docstatus) == 0
        and _discarding.get() == (doc.get("custom_supplier_retainer_batch"), doc.name)
    )


def validate_unissued_draft(invoice):
    if cint(invoice.docstatus) != 0:
        frappe.throw(_("Only draft invoices can be discarded by cancelling a retainer batch."))
    if (invoice.get("ncf") or invoice.get("encf_status")
            or invoice.get("ncf_status") not in (None, "", "Never Sent")):
        frappe.throw(_("Invoice {0} has fiscal processing information. Resolve it in Nubef before cancelling this batch.").format(invoice.name))


def _series_snapshot(invoice):
    """Preserve the naming counter that Frappe's normal deletion may rewind."""
    from frappe.model.naming import parse_naming_series

    series = invoice.get("naming_series")
    if not series:
        return None
    if ".#" in series:
        prefix, hashes = series.rsplit(".", 1)
        if "#" not in hashes:
            import re
            match = re.search("#+", series)
            if not match:
                return None
            prefix = prefix.replace(match.group(), "")
    else:
        prefix = series
    if "." in prefix:
        prefix = parse_naming_series(prefix.split("."), doc=invoice)
    rows = frappe.db.sql("SELECT current FROM `tabSeries` WHERE name=%s FOR UPDATE", (prefix,))
    return (prefix, rows[0][0]) if rows else None


def discard_batch_drafts(batch):
    """Validate the whole set first; clear only owned links and keep all hooks."""
    from powerpro.retainers.service import CLAIM, _lock_agreements

    batch.check_permission("cancel")
    point = "retainer_cancel_" + uuid4().hex
    frappe.db.savepoint(point)
    prior_links = [row.purchase_invoice for row in batch.details]
    try:
        _lock_agreements(batch)
        drafts = []
        for row in sorted(batch.details, key=lambda entry: entry.purchase_invoice or ""):
            if not row.purchase_invoice:
                continue
            records = frappe.db.sql("SELECT * FROM `tabPurchase Invoice` WHERE name=%s FOR UPDATE",
                                    (row.purchase_invoice,), as_dict=True)
            if not records:
                frappe.throw(_("Linked invoice {0} is missing. Review the batch history before cancelling.").format(row.purchase_invoice))
            invoice = frappe.get_doc(dict(records[0], doctype="Purchase Invoice"))
            if cint(invoice.docstatus) == 2:
                continue
            if cint(invoice.docstatus) == 1:
                frappe.throw(_("Cancel submitted purchase invoice {0} before cancelling this batch.").format(invoice.name))
            validate_unissued_draft(invoice)
            invoice.check_permission("delete")
            # File deletion can touch the filesystem outside the SQL savepoint.
            # Require an explicit attachment review instead of risking partial loss.
            if frappe.db.exists("File", {"attached_to_doctype": "Purchase Invoice", "attached_to_name": invoice.name}):
                frappe.throw(_("Invoice {0} has attachments. Review and preserve those files before discarding the draft.").format(invoice.name))
            if invoice.get("custom_supplier_retainer_batch") != batch.name:
                frappe.throw(_("The invoice does not belong to this retainer batch."))
            claims = frappe.db.sql("SELECT * FROM `tabSupplier Retainer Claim` WHERE name=%s FOR UPDATE",
                                   (invoice.get("custom_supplier_retainer_claim"),), as_dict=True)
            if (not claims or claims[0].batch != batch.name
                    or claims[0].purchase_invoice != invoice.name
                    or claims[0].agreement != row.agreement):
                frappe.throw(_("The invoice's period reservation does not match this batch."))
            drafts.append((row, invoice, frappe.get_doc(dict(claims[0], doctype=CLAIM))))

        discarded = []
        for row, invoice, claim in drafts:
            counter = _series_snapshot(invoice)
            # The parent is currently cancelling. Only these two source links
            # are cleared; all other Frappe/Nubef link and fiscal checks still run.
            claim.purchase_invoice = None
            claim.flags.retainer_service = True
            claim.save(ignore_permissions=True)
            row.db_set("purchase_invoice", None, update_modified=False)
            with discarding_draft(batch.name, invoice.name):
                frappe.delete_doc("Purchase Invoice", invoice.name, ignore_missing=False)
            if counter:
                frappe.db.set_value("Series", counter[0], "current", counter[1], update_modified=False)
            discarded.append(invoice.name)
        if discarded:
            batch.add_comment("Info", _("Draft purchase invoices discarded on batch cancellation: {0}. The original snapshots are retained in Deleted Document.").format(", ".join(escape_html(name) for name in discarded)))
    except Exception:
        frappe.db.rollback(save_point=point)
        for row, prior in zip(batch.details, prior_links):
            row.purchase_invoice = prior
        raise


def claim_is_released(claim):
    if claim.purchase_invoice:
        return False
    rows = frappe.db.sql("SELECT docstatus FROM `tabSupplier Retainer Batch` WHERE name=%s FOR UPDATE", (claim.batch,))
    return bool(rows and cint(rows[0][0]) == 2)
