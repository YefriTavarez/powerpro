import frappe

from erpnext.accounts.doctype.payment_entry import payment_entry


class PaymentEntry(payment_entry.PaymentEntry):
    @frappe.whitelist()
    def get_retention_details(self, retention_id, reference_doctype, reference_name):
        retention = self.get_retention(retention_id)

        reference = frappe.get_doc(reference_doctype, reference_name)
        
        # retention.retention_type -> "ISR" | "ITBIS"

        # apply retention rate on reference.total_taxes_and_charges
        # if retention.retention_type == "ITBIS" otherwise
        # apply retention rate on reference.grand_total

        # retention.retention_rate -> 10% | 15% | 20% | 25% | 30% | etc

        if retention.retention_type == "ITBIS":
            amount = reference.base_total_taxes_and_charges * retention.retention_rate / 100.0
        else:
            amount = reference.total * retention.retention_rate / 100.0

        return {
            "amount": amount,
            "cost_center": retention.cost_center,
            "account": retention.account,
            "retention_type": retention.retention_type,
            "retention_rate": retention.retention_rate,
            "retention_description": retention.retention_description,
            "retention_category": retention.retention_category,
        }

    @frappe.whitelist()
    def get_subtotal(self, reference_doctype, reference_name, isr_rate):
        doc = frappe.get_doc(reference_doctype, reference_name)

        return doc.total * isr_rate / 100.0

    def get_retention(self, name):
        doctype = "Retention"
        return frappe.get_doc(doctype, name)
