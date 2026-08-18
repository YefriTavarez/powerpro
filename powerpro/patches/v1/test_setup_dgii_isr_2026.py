import unittest
from unittest.mock import call, patch

from powerpro.patches.v1 import setup_dgii_isr_2026


class SetupDgiiIsr2026Test(unittest.TestCase):
	@patch.object(setup_dgii_isr_2026, "frappe")
	def test_resolves_production_and_legacy_component_names(self, frappe):
		frappe.db.exists.side_effect = lambda doctype, name: name in {
			"Impuesto Sobre la Renta Mensual",
			"ISR",
		}

		self.assertEqual(
			setup_dgii_isr_2026.get_existing_isr_component_names(),
			("Impuesto Sobre la Renta Mensual", "ISR"),
		)

	@patch.object(setup_dgii_isr_2026, "frappe")
	def test_updates_matching_structure_rows(self, frappe):
		frappe.db.exists.return_value = True
		frappe.get_all.return_value = ["row-production", "row-legacy"]

		updated = setup_dgii_isr_2026.update_salary_structure_isr_rows(
			"General Quincenal",
			("Impuesto Sobre la Renta Mensual", "ISR"),
		)

		self.assertEqual(updated, 2)
		self.assertEqual(frappe.db.set_value.call_count, 2)
		self.assertEqual(
			frappe.db.set_value.call_args_list,
			[
				call(
					"Salary Detail",
					row_name,
					{
						"amount_based_on_formula": 1,
						"formula": setup_dgii_isr_2026.ISR_FORMULA,
						"condition": setup_dgii_isr_2026.ISR_CONDITION,
						"variable_based_on_taxable_salary": 0,
					},
					update_modified=False,
				)
				for row_name in ("row-production", "row-legacy")
			],
		)


if __name__ == "__main__":
	unittest.main()
