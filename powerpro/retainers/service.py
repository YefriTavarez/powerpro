"""Prepare supplier purchases using ordinary Frappe document transactions.

An agreement row is the serialization lock; a durable claim records each billed
period. Neither cancellation nor amendment recycles a billed period silently.
"""

from decimal import Decimal, InvalidOperation
from uuid import uuid4

import frappe
from frappe import _
from frappe.utils import getdate

from powerpro.retainers.periods import claim_key, period_bounds


AGREEMENT = "Supplier Retainer Agreement"
BATCH = "Supplier Retainer Batch"
CLAIM = "Supplier Retainer Claim"


def validate_agreement(doc):
    try:
        amount = Decimal(str(doc.gross_amount))
        valid_amount = amount.is_finite() and amount > 0
    except (InvalidOperation, TypeError, ValueError):
        valid_amount = False
    if not valid_amount:
        frappe.throw(_("Gross Amount must be greater than zero."))
    if not doc.start_date:
        frappe.throw(_("Start Date is required."))
    if doc.end_date and getdate(doc.end_date) < getdate(doc.start_date):
        frappe.throw(_("End Date cannot precede Start Date."))
    period_bounds(getdate(doc.start_date), doc.frequency)
    supplier = frappe.get_doc("Supplier", doc.supplier)
    supplier.check_permission("read")
    if supplier.get("disabled"):
        frappe.throw(_("The supplier is disabled."))
    item = frappe.get_doc("Item", doc.item)
    item.check_permission("read")
    if item.get("disabled") or item.get("is_stock_item") or not item.get("is_purchase_item"):
        frappe.throw(_("Select an enabled non-stock purchase item for the service."))
    account = frappe.get_doc("Account", doc.expense_account)
    if account.company != doc.company or account.is_group or account.get("disabled") or account.root_type != "Expense":
        frappe.throw(_("Expense Account must be an enabled expense ledger of the agreement company."))
    cost_center = frappe.get_doc("Cost Center", doc.cost_center)
    if cost_center.company != doc.company or cost_center.is_group or cost_center.get("disabled"):
        frappe.throw(_("Cost Center must be an enabled leaf of the agreement company."))
    template = frappe.get_doc("Purchase Taxes and Charges Template", doc.taxes_and_charges)
    template.check_permission("read")
    if template.company != doc.company or template.get("disabled"):
        frappe.throw(_("The purchase tax template must be enabled and belong to the agreement company."))


def agreement_identity(agreement):
    """Return the original agreement so amendments cannot bypass billing claims."""
    current = agreement
    visited = set()
    while current.get("amended_from"):
        if current.name in visited:
            frappe.throw(_("The agreement amendment chain contains a cycle."))
        visited.add(current.name)
        current = frappe.get_doc(AGREEMENT, current.amended_from)
    return current.name


def batch_period(batch):
    if not batch.period_date:
        frappe.throw(_("Select a period date before loading agreements."))
    start, end = period_bounds(getdate(batch.period_date), batch.frequency)
    batch.period_start, batch.period_end = start, end
    return start, end


def snapshot_agreement(agreement, batch):
    agreement.check_permission("read")
    start, end = batch_period(batch)
    if agreement.docstatus != 1:
        frappe.throw(_("Agreement {0} must be submitted.").format(agreement.name))
    if agreement.company != batch.company or agreement.currency != batch.currency:
        frappe.throw(_("Agreement {0} has a different company or currency.").format(agreement.name))
    if agreement.frequency != batch.frequency:
        frappe.throw(_("Agreement {0} has a different frequency.").format(agreement.name))
    if getdate(agreement.start_date) > start or (agreement.end_date and getdate(agreement.end_date) < end):
        frappe.throw(_("Agreement {0} does not cover the full period. Proration is not supported.").format(agreement.name))
    validate_agreement(agreement)
    values = {field: agreement.get(field) for field in (
        "supplier", "item", "gross_amount", "currency", "taxes_and_charges",
        "expense_account", "cost_center", "description",
    )}
    values.update(agreement=agreement.name, period_start=start, period_end=end)
    return values


def refresh_batch(batch):
    batch_period(batch)
    seen = set()
    amount = Decimal("0")
    for row in batch.details:
        if not row.agreement:
            frappe.throw(_("Each row must select an agreement."))
        agreement = frappe.get_doc(AGREEMENT, row.agreement)
        identity = agreement_identity(agreement)
        if identity in seen:
            frappe.throw(_("An agreement can only appear once in a batch."))
        seen.add(identity)
        for field, value in snapshot_agreement(agreement, batch).items():
            row.set(field, value)
        amount += Decimal(str(row.gross_amount))
    batch.total_amount = amount


def _lock_agreements(batch):
    identities = {}
    for row in batch.details:
        agreement = frappe.get_doc(AGREEMENT, row.agreement)
        identities[row.agreement] = agreement_identity(agreement)
    # All versions lock the original row, even after it has been cancelled.
    names = sorted(set(identities) | set(identities.values()))
    if names:
        frappe.db.sql(
            "SELECT name FROM `tabSupplier Retainer Agreement` WHERE name IN %(names)s ORDER BY name FOR UPDATE",
            {"names": tuple(names)},
        )
    return identities


def _current_agreement(name):
    # Locking reads see the latest committed template, not a transaction's old snapshot.
    rows = frappe.db.sql(
        "SELECT * FROM `tabSupplier Retainer Agreement` WHERE name = %s FOR UPDATE",
        (name,), as_dict=True,
    )
    if not rows:
        frappe.throw(_("The selected agreement no longer exists."))
    return frappe.get_doc(dict(rows[0], doctype=AGREEMENT))


def _reserve_claim(batch, row, identity):
    overlaps = frappe.db.sql(
        """SELECT * FROM `tabSupplier Retainer Claim`
        WHERE agreement_identity = %(identity)s
          AND period_start <= %(end)s AND period_end >= %(start)s
        ORDER BY name FOR UPDATE""",
        {"identity": identity, "start": batch.period_start, "end": batch.period_end},
        as_dict=True,
    )
    key = claim_key(identity, batch.period_start, batch.period_end)
    from powerpro.retainers.cancellation import claim_is_released
    released = [claim for claim in overlaps if claim_is_released(claim)]
    overlaps = [claim for claim in overlaps if claim not in released]
    if not overlaps and not row.replaces_invoice:
        reusable = next((claim for claim in released if claim.name == key), None)
        if reusable:
            claim = frappe.get_doc(dict(reusable, doctype=CLAIM))
            claim.agreement, claim.batch = row.agreement, batch.name
            claim.flags.retainer_service = True
            return claim.save(ignore_permissions=True)
    if overlaps:
        prior = overlaps[0]
        if len(overlaps) != 1 or prior.name != key:
            frappe.throw(_("Agreement {0} already has a billed overlapping period.").format(row.agreement))
        if not row.replaces_invoice or row.replaces_invoice != prior.purchase_invoice:
            frappe.throw(_("This agreement and period already have invoice {0}. Select it explicitly only to replace a cancelled invoice.").format(prior.purchase_invoice))
        invoice_status = frappe.db.sql(
            "SELECT docstatus FROM `tabPurchase Invoice` WHERE name = %s FOR UPDATE",
            (prior.purchase_invoice,),
        )
        if not invoice_status or invoice_status[0][0] != 2:
            frappe.throw(_("Only a cancelled purchase invoice can be replaced."))
        claim = frappe.get_doc(dict(prior, doctype=CLAIM))
        claim.agreement, claim.batch = row.agreement, batch.name
        claim.purchase_invoice = None
        claim.flags.retainer_service = True
        claim.save(ignore_permissions=True)
        return claim
    if row.replaces_invoice:
        frappe.throw(_("The replacement invoice does not belong to this agreement and period."))
    claim = frappe.get_doc({
        "doctype": CLAIM, "name": key, "agreement": row.agreement,
        "agreement_identity": identity, "period_start": batch.period_start,
        "period_end": batch.period_end, "batch": batch.name,
    })
    claim.flags.retainer_service = True
    return claim.insert(ignore_permissions=True)


def _prepare_invoice(batch, row, claim):
    invoice = frappe.get_doc({
        "doctype": "Purchase Invoice", "company": batch.company,
        "supplier": row.supplier, "currency": batch.currency,
        "posting_date": batch.posting_date, "bill_date": batch.posting_date,
        "taxes_and_charges": row.taxes_and_charges,
        "custom_supplier_retainer_agreement": row.agreement,
        "custom_supplier_retainer_batch": batch.name,
        "custom_supplier_retainer_period_start": batch.period_start,
        "custom_supplier_retainer_period_end": batch.period_end,
        "custom_supplier_retainer_claim": claim.name,
        "custom_supplier_retainer_tax_template": row.taxes_and_charges,
    })
    invoice.append("items", {
        "item_code": row.item, "qty": 1, "rate": row.gross_amount,
        "expense_account": row.expense_account, "cost_center": row.cost_center,
        "description": row.description or frappe.db.get_value("Item", row.item, "description"),
    })
    invoice.run_method("set_missing_values")
    # Item/supplier defaults may supply taxes. The agreement's chosen template wins.
    template = frappe.get_doc("Purchase Taxes and Charges Template", row.taxes_and_charges)
    invoice.set("taxes", [])
    for tax in template.taxes:
        values = tax.as_dict()
        for field in ("name", "parent", "parenttype", "parentfield", "doctype", "idx", "owner", "creation", "modified", "modified_by", "docstatus"):
            values.pop(field, None)
        invoice.append("taxes", values)
    invoice.taxes_and_charges = row.taxes_and_charges
    invoice.apply_tds = 0  # Explicit template carries the agreed purchase retention configuration.
    if invoice.meta.has_field("include_retention"):
        settings = frappe.get_single("DGII Settings")
        accounts = {
            config.account for config in settings.get("multi_other_tax_detail", [])
            if config.company == batch.company and config.tax_type == "itbis_retenido"
        }
        invoice.include_retention = int(any(tax.account_head in accounts for tax in invoice.taxes))
    invoice.run_method("calculate_taxes_and_totals")
    from powerpro.retainers.invoice_hooks import generating_invoice
    with generating_invoice(batch.name, row.agreement, claim.name):
        invoice.insert()  # Normal create permission, validation and custom-app hooks.
    if invoice.docstatus != 0:
        frappe.throw(_("The generated purchase invoice must remain in draft."))
    return invoice


def generate_invoices(batch):
    batch.check_permission("submit")
    if batch.is_new():
        frappe.throw(_("Save the draft batch before submitting it."))
    if not frappe.has_permission("Purchase Invoice", "create"):
        frappe.throw(_("Purchase Invoice create permission is required."), frappe.PermissionError)
    if not batch.details:
        frappe.throw(_("Select at least one agreement."))
    if not batch.posting_date:
        frappe.throw(_("Posting Date is required."))
    point = "retainer_" + uuid4().hex
    frappe.db.savepoint(point)
    old_links = [row.purchase_invoice for row in batch.details]
    try:
        identities = _lock_agreements(batch)
        seen = set()
        for row in batch.details:
            identity = identities[row.agreement]
            if identity in seen:
                frappe.throw(_("An agreement can only appear once in a batch."))
            seen.add(identity)
            if row.purchase_invoice:
                frappe.throw(_("This batch already has generated invoices."))
            agreement = _current_agreement(row.agreement)
            for field, value in snapshot_agreement(agreement, batch).items():
                row.set(field, value)
            claim = _reserve_claim(batch, row, identity)
            invoice = _prepare_invoice(batch, row, claim)
            claim.purchase_invoice = invoice.name
            claim.flags.retainer_service = True
            claim.save(ignore_permissions=True)
            row.purchase_invoice = invoice.name
        batch.total_amount = sum(Decimal(str(row.gross_amount)) for row in batch.details)
    except Exception:
        frappe.db.rollback(save_point=point)
        for row, prior in zip(batch.details, old_links):
            row.purchase_invoice = prior
        raise
