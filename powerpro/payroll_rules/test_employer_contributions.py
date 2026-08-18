from decimal import Decimal
from unittest import TestCase

from powerpro.payroll_rules.employer_contributions import calculate_employer_contributions


class TestEmployerContributions(TestCase):
	def test_standard_monthly_salary(self):
		rows = calculate_employer_contributions(50000, "2026-08-15")
		amounts = {row.code: row.amount for row in rows}
		self.assertEqual(amounts["AFP"], Decimal("3550.00"))
		self.assertEqual(amounts["ARS"], Decimal("3545.00"))
		self.assertEqual(amounts["INFOTEP"], Decimal("500.00"))
		self.assertEqual(amounts["SRL"], Decimal("600.00"))

	def test_commission_and_vacation_bases(self):
		rows = calculate_employer_contributions(
			50000,
			"2026-08-15",
			commissions=2500,
			statutory_vacation=1000,
		)
		by_code = {row.code: row for row in rows}
		self.assertEqual(by_code["INFOTEP"].base_amount, Decimal("52500.00"))
		self.assertEqual(by_code["INFOTEP"].amount, Decimal("525.00"))
		self.assertEqual(by_code["SRL"].base_amount, Decimal("53500.00"))
		self.assertEqual(by_code["SRL"].amount, Decimal("642.00"))

	def test_srl_ceiling_is_snapshotted(self):
		rows = calculate_employer_contributions(150000, "2026-08-15")
		srl = next(row for row in rows if row.code == "SRL")
		self.assertEqual(srl.base_amount, Decimal("92892.00"))
		self.assertEqual(srl.ceiling, Decimal("92892.00"))
		self.assertEqual(srl.amount, Decimal("1114.70"))

	def test_configured_rates_are_used(self):
		rows = calculate_employer_contributions(
			10000,
			"2026-08-15",
			infotep_rate_percent=Decimal("1.1"),
			srl_rate_percent=Decimal("1.3"),
		)
		amounts = {row.code: row.amount for row in rows}
		self.assertEqual(amounts["INFOTEP"], Decimal("110.00"))
		self.assertEqual(amounts["SRL"], Decimal("130.00"))
