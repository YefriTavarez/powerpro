import unittest

from powerpro.controllers.payroll_preflight import (
    _formula_has_cap,
    _is_dominican_id_shape,
    _money,
    _normalise_formula,
    _rate_matches,
)


class PayrollPreflightHelpersTest(unittest.TestCase):
    def test_personal_id_shape_accepts_digits_and_separators(self):
        self.assertTrue(_is_dominican_id_shape("001-1234567-8"))
        self.assertTrue(_is_dominican_id_shape("00112345678"))
        self.assertFalse(_is_dominican_id_shape("001-123456-8"))

    def test_formula_normalisation(self):
        self.assertEqual(_normalise_formula(" base * 0.0710 "), "base*0.0710")

    def test_formula_cap_detection(self):
        self.assertTrue(_formula_has_cap("min(base, ceiling) * 0.071"))
        self.assertFalse(_formula_has_cap("base * 0.071"))

    def test_rate_comparison(self):
        self.assertTrue(_rate_matches(2.87, 2.87))
        self.assertFalse(_rate_matches(2.86, 2.87))

    def test_money_rounding(self):
        self.assertEqual(_money(10.126), 10.13)
        self.assertEqual(_money(None), 0.0)


if __name__ == "__main__":
    unittest.main()
