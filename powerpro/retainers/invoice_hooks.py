"""Protect the source of retainer invoices without replacing fiscal controllers."""
from contextlib import contextmanager
from contextvars import ContextVar

import frappe
from frappe import _
from frappe.utils import cint, getdate


_generation = ContextVar("supplier_retainer_generation", default=None)
SOURCE_FIELDS = (
    "custom_supplier_retainer_agreement",
    "custom_supplier_retainer_batch",
    "custom_supplier_retainer_period_start",
    "custom_supplier_retainer_period_end",
    "custom_supplier_retainer_claim",
    "custom_supplier_retainer_tax_template",
)


@contextmanager
def generating_invoice(batch, agreement, claim):
    """Only the server-side batch generator can assign invoice provenance."""
    token = _generation.set((batch, agreement, claim))
    try:
        yield
    finally:
        _generation.reset(token)


def validate_source(doc, method=None):
    # A bench can host sites that have not installed the optional retainer fields.
    if not doc.meta.has_field("custom_supplier_retainer_claim"):
        return
    previous = doc.get_doc_before_save()
    linked = doc.get("custom_supplier_retainer_claim")
    if previous and previous.get("custom_supplier_retainer_claim"):
        for field in SOURCE_FIELDS + ("supplier", "company", "currency"):
            old, new = previous.get(field), doc.get(field)
            if field.endswith(("period_start", "period_end")) and old and new:
                old, new = getdate(old), getdate(new)
            if old != new:
                frappe.throw(_("No puede cambiar el origen de una factura de iguala."))
    elif linked or any(doc.get(field) for field in SOURCE_FIELDS):
        expected = (doc.get(SOURCE_FIELDS[1]), doc.get(SOURCE_FIELDS[0]), linked)
        if not doc.is_new() or _generation.get() != expected:
            frappe.throw(_("Las facturas de iguala se crean desde una Liquidación de Igualas."))

    if doc.is_new() and doc.get("amended_from"):
        original = frappe.db.get_value("Purchase Invoice", doc.amended_from, "custom_supplier_retainer_claim")
        if original and not linked:
            frappe.throw(_("Reemplace esta factura desde una nueva Liquidación de Igualas para conservar el control del período."))

    if not linked:
        return
    if cint(doc.get("docstatus")) != 2 and cint(frappe.db.get_single_value("Power-Pro Settings", "enforce_retainer_tax_template")):
        if doc.get("taxes_and_charges") != doc.get("custom_supplier_retainer_tax_template"):
            frappe.throw(_("La factura debe conservar la plantilla de impuestos utilizada al generar la iguala."))


def protect_delete(doc, method=None):
    if doc.get("custom_supplier_retainer_claim"):
        from powerpro.retainers.cancellation import may_discard, validate_unissued_draft
        if may_discard(doc):
            validate_unissued_draft(doc)
            return
        frappe.throw(_("Para descartar una factura de iguala en borrador, cancele su Liquidación de Igualas. Las facturas sometidas requieren su cancelación individual."))


def before_cancel(doc, method=None):
    if doc.get("custom_supplier_retainer_claim"):
        validate_source(doc)
        # These references are an audit trail, not dependent accounting entries.
        doc.ignore_linked_doctypes = tuple(set(doc.get("ignore_linked_doctypes") or ()) | {
            "Supplier Retainer Claim", "Supplier Retainer Batch",
        })
