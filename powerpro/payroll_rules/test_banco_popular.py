from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).with_name("banco_popular.py")
SPEC = spec_from_file_location("powerpro_banco_popular_pure", MODULE_PATH)
MODULE = module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

BankFileValidationError = MODULE.BankFileValidationError
BancoPopularProfile = MODULE.BancoPopularProfile
PayrollPayment = MODULE.PayrollPayment
build_payroll_file = MODULE.build_payroll_file


class TestBancoPopularPayrollFile(unittest.TestCase):
    def setUp(self):
        self.profile = BancoPopularProfile(
            activation_number="99999",
            company_identification="101010101",
            registered_company_name="EMPRESA DE PRUEBA",
        )

    def payment(self, **overrides):
        values = {
            "reference": "SAL-TEST-0001",
            "beneficiary_name": "EMPLEADO DE PRUEBA",
            "bank_account_no": "0012345678",
            "account_type": "Ahorro",
            "identification_type": "Cédula",
            "identification_number": "00112345678",
            "amount": Decimal("15500.00"),
        }
        values.update(overrides)
        return PayrollPayment(**values)

    def build(self, payments=None):
        return build_payroll_file(
            self.profile,
            payment_date=date(2026, 8, 14),
            payment_sequence="0000001",
            description="PAGO NOMINA PRUEBA",
            payments=payments or [self.payment()],
        )

    def test_builds_exact_fixed_width_layout(self):
        generated = self.build()
        self.assertEqual(generated.filename, "PE999990108140000001E.txt")
        self.assertEqual(generated.payment_count, 1)
        self.assertEqual(generated.total_amount, Decimal("15500.00"))
        self.assertTrue(generated.content.endswith(b"\r\n"))

        header, detail, final = generated.content.split(b"\r\n")
        self.assertEqual(final, b"")
        self.assertEqual(len(header), 320)
        self.assertEqual(len(detail), 320)

        self.assertEqual(header[0:1], b"H")
        self.assertEqual(header[1:16], b"101010101      ")
        self.assertEqual(header[16:51], b"EMPRESA DE PRUEBA                  ")
        self.assertEqual(header[51:58], b"0000001")
        self.assertEqual(header[58:60], b"01")
        self.assertEqual(header[60:68], b"20260814")
        self.assertEqual(header[92:103], b"00000000001")
        self.assertEqual(header[103:116], b"0000001550000")

        self.assertEqual(detail[0:16], b"N101010101      ")
        self.assertEqual(detail[16:23], b"0000001")
        self.assertEqual(detail[23:30], b"0000001")
        self.assertEqual(detail[30:50], b"0012345678          ")
        self.assertEqual(detail[50:51], b"2")
        self.assertEqual(detail[51:54], b"214")
        self.assertEqual(detail[54:63], b"101010708")
        self.assertEqual(detail[63:65], b"32")
        self.assertEqual(detail[65:78], b"0000001550000")
        self.assertEqual(detail[78:80], b"CE")
        self.assertEqual(detail[80:95], b"00112345678    ")
        self.assertEqual(detail[95:142], b"EMPLEADO DE PRUEBA                             ")
        self.assertEqual(detail[142:186], b"PAGO NOMINA PRUEBA" + (b" " * 26))
        self.assertEqual(detail[186:187], b"1")
        self.assertEqual(detail[187:320], b" " * 133)

    def test_reconciles_header_count_and_total(self):
        generated = self.build(
            [
                self.payment(reference="SAL-1", amount="10.01"),
                self.payment(reference="SAL-2", amount="20.02", account_type="Corriente"),
            ]
        )
        header, first, second, final = generated.content.split(b"\r\n")
        self.assertEqual(final, b"")
        self.assertEqual(header[92:103], b"00000000002")
        self.assertEqual(header[103:116], b"0000000003003")
        self.assertEqual(first[63:65], b"32")
        self.assertEqual(second[63:65], b"22")

    def test_normalizes_non_breaking_spaces_and_truncates_name_to_35(self):
        generated = self.build(
            [
                self.payment(
                    beneficiary_name="NOMBRE\u00a0MUY LARGO DE EMPLEADO PARA VALIDAR CORTE",
                )
            ]
        )
        detail = generated.content.split(b"\r\n")[1]
        self.assertNotIn(b"\xa0", detail)
        self.assertEqual(detail[95:130], b"NOMBRE MUY LARGO DE EMPLEADO PARA V")
        self.assertEqual(detail[130:142], b" " * 12)

    def test_normalizes_embedded_line_breaks(self):
        generated = self.build([self.payment(beneficiary_name="NOMBRE\nDE EMPLEADO")])
        detail = generated.content.split(b"\r\n")[1]
        self.assertEqual(detail[95:113], b"NOMBRE DE EMPLEADO")

    def test_rejects_non_popular_accounts(self):
        with self.assertRaisesRegex(BankFileValidationError, "only Banco Popular"):
            self.build([self.payment(bank_name="OTRO BANCO")])

        with self.assertRaisesRegex(BankFileValidationError, "only Banco Popular"):
            self.build([self.payment(bank_name="BANCO NO POPULAR")])

    def test_rejects_missing_account_type(self):
        with self.assertRaisesRegex(BankFileValidationError, "Account Type"):
            self.build([self.payment(account_type="")])

    def test_rejects_duplicate_salary_slip_reference(self):
        with self.assertRaisesRegex(BankFileValidationError, "Duplicate payment references"):
            self.build([self.payment(), self.payment()])

    def test_rejects_zero_amount(self):
        with self.assertRaisesRegex(BankFileValidationError, "greater than zero"):
            self.build([self.payment(amount="0")])

    def test_rejects_invalid_payment_sequence(self):
        with self.assertRaisesRegex(BankFileValidationError, "exactly 7 digits"):
            build_payroll_file(
                self.profile,
                payment_date=date(2026, 8, 14),
                payment_sequence="1",
                description="PAGO NOMINA PRUEBA",
                payments=[self.payment()],
            )

    def test_rejects_empty_payment_description(self):
        with self.assertRaisesRegex(BankFileValidationError, "Description is required"):
            build_payroll_file(
                self.profile,
                payment_date=date(2026, 8, 14),
                payment_sequence="0000001",
                description="",
                payments=[self.payment()],
            )

    def test_accepts_alphanumeric_passport(self):
        generated = self.build(
            [
                self.payment(
                    identification_type="Pasaporte",
                    identification_number="ab123456",
                )
            ]
        )
        detail = generated.content.split(b"\r\n")[1]
        self.assertEqual(detail[78:80], b"PS")
        self.assertEqual(detail[80:95], b"AB123456       ")

    def test_rejects_changed_v1_routing_code(self):
        profile = BancoPopularProfile(
            activation_number="99999",
            company_identification="101010101",
            registered_company_name="EMPRESA DE PRUEBA",
            routing_code="999999999",
        )
        with self.assertRaisesRegex(BankFileValidationError, "requires Routing Code"):
            build_payroll_file(
                profile,
                payment_date=date(2026, 8, 14),
                payment_sequence="0000001",
                description="PAGO NOMINA PRUEBA",
                payments=[self.payment()],
            )


if __name__ == "__main__":
    unittest.main()
