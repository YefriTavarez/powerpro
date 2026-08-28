# Copyright (c) 2026, PowerPro contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from powerpro.payroll_rules.banco_popular import (
    BankFileValidationError,
    BancoPopularProfile,
    validate_profile,
)


class BankFileProfile(Document):
    def validate(self):
        if self.format_version != "Banco Popular Nómina v1":
            frappe.throw(_("Unsupported bank format version."))
        try:
            validate_profile(
                BancoPopularProfile(
                    activation_number=self.activation_number,
                    company_identification=self.company_identification,
                    registered_company_name=self.registered_company_name,
                    service_code=self.service_code,
                    routing_code=self.routing_code,
                    currency=self.currency,
                    contact_method=self.contact_method,
                    file_prefix=self.file_prefix,
                    file_suffix=self.file_suffix,
                )
            )
        except BankFileValidationError as exc:
            frappe.throw(str(exc), title=_("Bank validation blocked"))
        if self.is_default:
            existing = frappe.db.exists(
                "Bank File Profile",
                {
                    "company": self.company,
                    "is_default": 1,
                    "name": ["!=", self.name or ""],
                },
            )
            if existing:
                frappe.throw(
                    _("Company {0} already has default Bank File Profile {1}.").format(
                        frappe.bold(self.company), frappe.bold(existing)
                    )
                )
