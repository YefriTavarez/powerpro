# Copyright (c) 2026, PowerPro contributors
# For license information, please see license.txt

from __future__ import annotations

from decimal import Decimal

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime
from frappe.utils.file_manager import save_file

from powerpro.payroll_rules.banco_popular import (
    BankFileValidationError,
    BancoPopularProfile,
    PayrollPayment,
    build_payroll_file,
    validate_batch_instruction,
    validate_payment,
    validate_profile,
)


class PayrollBankBatch(Document):
    def validate(self):
        self._validate_source_documents()
        self._validate_unique_sequence()
        self._refresh_validation_snapshot()

    def before_submit(self):
        if self.validation_status != "Ready":
            frappe.throw(
                _("The payroll bank batch must be Ready before approval."),
                title=_("Bank validation blocked"),
            )
        self._validate_salary_slips_not_in_another_batch()

    def on_submit(self):
        self.status = "Approved"

    def on_cancel(self):
        self.db_set("status", "Cancelled", update_modified=False)

    @frappe.whitelist()
    def load_payments(self):
        """Snapshot submitted, non-withheld Salary Slips into this draft batch."""
        self.check_permission("write")
        if self.docstatus != 0:
            frappe.throw(_("Payments can only be loaded into a draft batch."))
        self._validate_source_documents()
        for doctype in ("Salary Slip", "Employee"):
            if not frappe.has_permission(doctype, "read"):
                frappe.throw(
                    _("Read permission for {0} is required to load bank payments.").format(
                        frappe.bold(doctype)
                    ),
                    frappe.PermissionError,
                )

        slips = frappe.get_all(
            "Salary Slip",
            filters={
                "payroll_entry": self.payroll_entry,
                "docstatus": 1,
                "status": ["!=", "Withheld"],
            },
            fields=[
                "name",
                "employee",
                "employee_name",
                "bank_name",
                "bank_account_no",
                "currency",
                "net_pay",
            ],
            order_by="employee_name asc, name asc",
        )
        if not slips:
            frappe.throw(
                _("Payroll Entry {0} has no submitted payable Salary Slips.").format(
                    frappe.bold(self.payroll_entry)
                )
            )

        employee_names = [row.employee for row in slips]
        employee_fields = [
            "name",
            "employee_name",
            "bank_name",
            "bank_ac_no",
            "custom_bank_account_type",
            "custom_bank_identification_type",
            "custom_bank_identification_number",
        ]
        if frappe.get_meta("Employee").has_field("custom_personal_id"):
            employee_fields.append("custom_personal_id")
        employees = {
            row.name: row
            for row in frappe.get_all(
                "Employee",
                filters={"name": ["in", employee_names]},
                fields=employee_fields,
            )
        }

        self.set("details", [])
        for slip in slips:
            employee = employees.get(slip.employee) or frappe._dict()
            self.append(
                "details",
                {
                    "salary_slip": slip.name,
                    "employee": slip.employee,
                    "employee_name": slip.employee_name or employee.employee_name,
                    "bank_name": slip.bank_name or employee.bank_name,
                    "bank_account_no": slip.bank_account_no or employee.bank_ac_no,
                    "account_type": employee.custom_bank_account_type,
                    "currency": slip.currency,
                    "amount": slip.net_pay,
                    "identification_type": employee.custom_bank_identification_type or "Cédula",
                    "identification_number": (
                        employee.custom_bank_identification_number
                        or employee.get("custom_personal_id")
                    ),
                    "validation_status": "Pending",
                },
            )

        self.save()
        return {
            "payment_count": self.payment_count,
            "total_amount": self.total_amount,
            "validation_status": self.validation_status,
            "validation_messages": self.validation_messages,
        }

    @frappe.whitelist()
    def generate_file(self):
        """Create one immutable private TXT from an approved batch snapshot."""
        self.check_permission("write")
        self.reload()
        if self.docstatus != 1 or self.status not in ("Approved", "Generated"):
            frappe.throw(_("Submit and approve the batch before generating the bank file."))
        if self.generated_file and self.file_hash:
            return self._file_response(reused=True)

        generated = self._build_file()
        if generated.payment_count != self.payment_count or generated.total_amount != Decimal(
            str(self.total_amount)
        ).quantize(Decimal("0.01")):
            frappe.throw(
                _("The approved count or total no longer matches the generated file."),
                title=_("Snapshot mismatch"),
            )

        file_doc = save_file(
            generated.filename,
            generated.content,
            self.doctype,
            self.name,
            is_private=1,
        )
        values = {
            "status": "Generated",
            "generated_file": file_doc.file_url,
            "file_name": generated.filename,
            "file_hash": generated.sha256,
            "generated_by": frappe.session.user,
            "generated_on": now_datetime(),
        }
        self.db_set(values)
        self.reload()
        return self._file_response(reused=False)

    def _validate_source_documents(self):
        if not all((self.payroll_entry, self.profile, self.company, self.currency)):
            return

        entry = frappe.get_cached_doc("Payroll Entry", self.payroll_entry)
        entry.check_permission("read")
        if entry.docstatus != 1:
            frappe.throw(_("Payroll Entry {0} must be submitted.").format(frappe.bold(entry.name)))
        if entry.company != self.company:
            frappe.throw(_("Payroll Entry company does not match the batch company."))
        if entry.currency != self.currency:
            frappe.throw(_("Payroll Entry currency does not match the batch currency."))

        profile = frappe.get_cached_doc("Bank File Profile", self.profile)
        profile.check_permission("read")
        if not profile.enabled:
            frappe.throw(_("Bank File Profile {0} is disabled.").format(frappe.bold(profile.name)))
        if profile.company != self.company:
            frappe.throw(_("Bank File Profile company does not match the Payroll Entry."))
        if profile.currency != self.currency:
            frappe.throw(_("Bank File Profile currency does not match the Payroll Entry."))
        try:
            validate_profile(_profile_data(profile))
            if self.payment_date and self.payment_sequence and self.payment_description:
                validate_batch_instruction(
                    payment_date=getdate(self.payment_date),
                    payment_sequence=self.payment_sequence,
                    description=self.payment_description,
                )
        except BankFileValidationError as exc:
            frappe.throw(str(exc), title=_("Bank validation blocked"))

    def _validate_unique_sequence(self):
        duplicate = frappe.db.exists(
            "Payroll Bank Batch",
            {
                "profile": self.profile,
                "payment_date": self.payment_date,
                "payment_sequence": self.payment_sequence,
                "name": ["!=", self.name or ""],
            },
        )
        if duplicate:
            frappe.throw(
                _("Payment Sequence {0} is already used on {1} by batch {2}.").format(
                    frappe.bold(self.payment_sequence),
                    frappe.bold(self.payment_date),
                    frappe.bold(duplicate),
                )
            )

    def _refresh_validation_snapshot(self):
        if not self.details:
            self.validation_status = "Pending"
            self.validation_messages = _("Load submitted Salary Slips before approval.")
            self.payment_count = 0
            self.total_amount = 0
            return

        profile = validate_profile(
            _profile_data(frappe.get_cached_doc("Bank File Profile", self.profile))
        )
        errors = []
        for row in self.details:
            try:
                validate_payment(_payment_data(row), profile)
                row.validation_status = "Ready"
                row.validation_message = ""
            except BankFileValidationError as exc:
                row.validation_status = "Blocked"
                row.validation_message = str(exc)
                errors.append(str(exc))

        self.payment_count = len(self.details)
        self.total_amount = sum(
            (Decimal(str(row.amount or 0)) for row in self.details), Decimal("0.00")
        )
        if errors:
            self.validation_status = "Blocked"
            self.validation_messages = "\n".join(errors[:50])
            return

        try:
            generated = self._build_file()
        except BankFileValidationError as exc:
            self.validation_status = "Blocked"
            self.validation_messages = str(exc)
            return

        self.payment_count = generated.payment_count
        self.total_amount = generated.total_amount
        self.validation_status = "Ready"
        self.validation_messages = _(
            "Ready: {0} payments reconcile to {1}. No bank or accounting entry was created."
        ).format(generated.payment_count, generated.total_amount)

    def _validate_salary_slips_not_in_another_batch(self):
        details = frappe.qb.DocType("Payroll Bank Batch Detail")
        batches = frappe.qb.DocType("Payroll Bank Batch")
        salary_slips = [row.salary_slip for row in self.details]
        duplicates = (
            frappe.qb.from_(details)
            .inner_join(batches)
            .on(details.parent == batches.name)
            .select(details.salary_slip, details.parent)
            .where(
                (details.salary_slip.isin(salary_slips))
                & (batches.docstatus < 2)
                & (batches.name != self.name)
            )
        ).run(as_dict=True)
        if duplicates:
            frappe.throw(
                _("Salary Slip {0} is already included in active batch {1}.").format(
                    frappe.bold(duplicates[0].salary_slip), frappe.bold(duplicates[0].parent)
                )
            )

    def _build_file(self):
        profile = frappe.get_cached_doc("Bank File Profile", self.profile)
        return build_payroll_file(
            _profile_data(profile),
            payment_date=getdate(self.payment_date),
            payment_sequence=self.payment_sequence,
            description=self.payment_description,
            payments=[_payment_data(row) for row in self.details],
        )

    def _file_response(self, *, reused):
        return {
            "file_url": self.generated_file,
            "file_name": self.file_name,
            "sha256": self.file_hash,
            "payment_count": self.payment_count,
            "total_amount": self.total_amount,
            "reused": reused,
            "bank_entry_created": False,
        }


def _profile_data(profile):
    return BancoPopularProfile(
        activation_number=profile.activation_number,
        company_identification=profile.company_identification,
        registered_company_name=profile.registered_company_name,
        service_code=profile.service_code,
        routing_code=profile.routing_code,
        currency=profile.currency,
        contact_method=profile.contact_method,
        file_prefix=profile.file_prefix,
        file_suffix=profile.file_suffix,
    )


def _payment_data(row):
    return PayrollPayment(
        reference=row.salary_slip,
        beneficiary_name=row.employee_name,
        bank_account_no=row.bank_account_no,
        account_type=row.account_type,
        identification_type=row.identification_type,
        identification_number=row.identification_number,
        amount=Decimal(str(row.amount or 0)),
        bank_name=row.bank_name,
        currency=row.currency,
    )


@frappe.whitelist()
def get_default_profile(company):
    if not frappe.has_permission("Bank File Profile", "read"):
        frappe.throw(_("Not permitted to read Bank File Profile."), frappe.PermissionError)
    return frappe.db.get_value(
        "Bank File Profile",
        {"company": company, "enabled": 1, "is_default": 1},
        "name",
    )
