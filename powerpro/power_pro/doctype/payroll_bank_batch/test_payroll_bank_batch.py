"""Draft/save/load regressions using Frappe's real document persistence.

Source documents are synthetic so these tests never alter payroll. Each test
rolls its batch writes back to a savepoint. Run only on a development/test site.
"""

import unittest
from decimal import Decimal
from unittest.mock import patch

import frappe

from powerpro.power_pro.doctype.payroll_bank_batch import payroll_bank_batch as controller


class TestPayrollBankBatchDraft(unittest.TestCase):
    def setUp(self):
        self.savepoint = "bank_batch_draft_regression"
        frappe.db.savepoint(self.savepoint)
        self.addCleanup(lambda: frappe.db.rollback(save_point=self.savepoint))
        self.profile = frappe._dict(
            activation_number="99999",
            company_identification="101010101",
            registered_company_name="EMPRESA DE PRUEBA",
            service_code="01",
            routing_code="101010708",
            currency="DOP",
            contact_method="1",
            file_prefix="PE",
            file_suffix="E",
        )
        original_get_cached_doc = frappe.get_cached_doc

        def get_cached_doc(doctype, name=None, *args, **kwargs):
            if doctype == "Bank File Profile" and name == "_Test Bank Profile":
                return self.profile
            return original_get_cached_doc(doctype, name, *args, **kwargs)

        profile_patch = patch.object(frappe, "get_cached_doc", side_effect=get_cached_doc)
        source_patch = patch.object(
            controller.PayrollBankBatch, "_validate_source_documents", return_value=None
        )
        profile_patch.start()
        source_patch.start()
        self.addCleanup(profile_patch.stop)
        self.addCleanup(source_patch.stop)

    def batch(self):
        batch = frappe.get_doc(
            {
                "doctype": "Payroll Bank Batch",
                "payroll_entry": "_Test Bank Payroll Entry",
                "profile": "_Test Bank Profile",
                "company": "_Test Bank Company",
                "currency": "DOP",
                "payment_date": "2099-01-01",
                "payment_sequence": "9999991",
                "payment_description": "PRUEBA DE BORRADOR",
            }
        )
        batch.flags.ignore_links = True  # Synthetic sources, never create Salary Slips.
        return batch

    def payment(self, **changes):
        row = {
            "salary_slip": "_Test-Bank-Salary-Slip",
            "employee": "_Test Bank Employee",
            "employee_name": "EMPLEADO DE PRUEBA",
            "bank_name": "BANCO POPULAR DOMINICANO",
            "bank_account_no": "0001234567",
            "account_type": "Ahorro",
            "currency": "DOP",
            "amount": 123.45,
            "identification_type": "Cédula",
            "identification_number": "00112345678",
        }
        row.update(changes)
        return row

    def test_empty_draft_saves_and_cannot_be_submitted(self):
        batch = self.batch().insert()
        batch.reload()
        self.assertEqual(batch.details, [])
        self.assertEqual(batch.validation_status, "Pending")
        self.assertEqual(batch.payment_count, 0)
        self.assertEqual(batch.total_amount, 0)
        with self.assertRaises(frappe.ValidationError):
            batch.submit()
        self.assertEqual(frappe.db.get_value(batch.doctype, batch.name, "docstatus"), 0)

    def test_legacy_placeholder_row_is_removed_before_save(self):
        batch = self.batch()
        batch.append(
            "details", {"currency": "DOP", "identification_type": "Cédula"}
        )
        batch.insert()
        batch.reload()
        self.assertEqual(batch.details, [])
        self.assertEqual(batch.validation_status, "Pending")

    def test_partial_payment_is_not_discarded(self):
        batch = self.batch()
        batch.append("details", {"employee_name": "PARTIAL PAYMENT"})
        with self.assertRaises(frappe.MandatoryError):
            batch.insert()
        self.assertEqual(len(batch.details), 1)
        self.assertEqual(batch.details[0].employee_name, "PARTIAL PAYMENT")

    def test_missing_bank_fields_save_blocked_and_cannot_be_submitted(self):
        batch = self.batch()
        batch.append(
            "details",
            self.payment(bank_account_no="", account_type="", identification_number=""),
        )
        batch.insert()
        batch.reload()
        self.assertEqual(len(batch.details), 1)
        self.assertEqual(batch.validation_status, "Blocked")
        self.assertTrue(batch.details[0].validation_message)
        with self.assertRaises(frappe.ValidationError):
            batch.submit()

    def test_zero_amount_saves_as_blocked(self):
        batch = self.batch()
        batch.append("details", self.payment(amount=0))
        batch.insert()
        batch.reload()
        self.assertEqual(batch.validation_status, "Blocked")
        self.assertIn("greater than zero", batch.validation_messages)

    def test_valid_snapshot_submits_and_persists_approved_status(self):
        batch = self.batch()
        batch.append("details", self.payment())
        batch.insert()
        self.assertEqual(batch.validation_status, "Ready")
        batch.submit()
        batch.reload()
        self.assertEqual(batch.docstatus, 1)
        self.assertEqual(batch.status, "Approved")
        self.assertEqual(batch.payment_count, 1)
        self.assertEqual(Decimal(str(batch.total_amount)), Decimal("123.45"))
        with self.assertRaises(frappe.ValidationError):
            batch.load_payments()

    def test_load_payments_saves_incomplete_bank_data_for_review(self):
        batch = self.batch().insert()
        slip = frappe._dict(
            name="_Test-Bank-Salary-Slip",
            employee="_Test Bank Employee",
            employee_name="EMPLEADO DE PRUEBA",
            bank_name="BANCO POPULAR DOMINICANO",
            bank_account_no="0001234567",
            currency="DOP",
            net_pay=123.45,
        )
        employee = frappe._dict(
            name=slip.employee,
            custom_bank_account_type="",
            custom_bank_identification_type="Cédula",
            custom_bank_identification_number="00112345678",
        )
        original_get_all = frappe.get_all

        def source_rows(doctype, *args, **kwargs):
            if doctype == "Salary Slip":
                self.assertEqual(kwargs["filters"]["docstatus"], 1)
                self.assertEqual(kwargs["filters"]["status"], ["!=", "Withheld"])
                return [slip]
            if doctype == "Employee":
                return [employee]
            return original_get_all(doctype, *args, **kwargs)

        with patch.object(frappe, "get_all", side_effect=source_rows):
            result = batch.load_payments()
        batch.reload()
        self.assertEqual(result["validation_status"], "Blocked")
        self.assertEqual(batch.details[0].salary_slip, slip.name)
        self.assertIn("Account Type", batch.details[0].validation_message)

    def test_draft_cannot_generate_a_file(self):
        batch = self.batch().insert()
        with patch.object(controller, "save_file") as save_file:
            with self.assertRaises(frappe.ValidationError):
                batch.generate_file()
            save_file.assert_not_called()

    def test_header_mandatory_fields_still_apply(self):
        batch = self.batch()
        batch.payment_description = ""
        with self.assertRaises(frappe.MandatoryError):
            batch.insert()
