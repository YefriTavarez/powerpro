"""List visibility for the explicitly selected business documents.

This is a permission-query filter, not a document access restriction. Historical
records, direct links, permission-bypassing queries and core sharing stay intact.
"""

import frappe


FILTERED_DOCTYPES = frozenset({
    "Additional Salary", "Asset Maintenance Log", "Attendance", "Delivery Note",
    "Income Tax Slab", "Journal Entry", "Leave Allocation", "Leave Application",
    "Overtime Settlement Election", "Payment Entry", "Payment Ledger Entry",
    "Payroll Bank Batch", "Purchase Invoice", "Quotation",
    "Retroactive Overtime Adjustment", "Salary Slip", "Salary Structure Assignment",
    "Sales Invoice", "Supplier Retainer Batch",
})

# Preserve PowerPro's existing visibility restrictions on these DocTypes.
EXISTING_CONDITIONS = {
    "Asset Maintenance Log": "powerpro.utils.query.asset_maintenance_log_query_conditions",
    "Delivery Note": "powerpro.utils.query.delivery_note_query_conditions",
    "Payment Entry": "powerpro.utils.query.payment_entry_query_conditions",
    "Quotation": "powerpro.utils.query.quotation_query_conditions",
    "Sales Invoice": "powerpro.utils.query.sales_invoice_query_conditions",
}


def query_conditions(user=None, doctype=None):
    # Only literal allowlisted names may become SQL identifiers. In particular,
    # Supplier Retainer Agreement must remain visible after cancellation.
    if doctype not in FILTERED_DOCTYPES:
        return ""
    active = f"`tab{doctype}`.`docstatus` != 2"
    previous_method = EXISTING_CONDITIONS.get(doctype)
    if previous_method:
        previous = frappe.get_attr(previous_method)(user)
        if previous:
            # Group legacy OR clauses so neither branch can expose cancellations.
            return f"({previous}) AND ({active})"
    return active
