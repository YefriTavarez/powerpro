import unittest

from powerpro.manufacturing_pro.doctype.raw_material.batch_series import (
	build_batch_number_series,
	extract_initials,
	extract_pt,
)


class TestRawMaterialBatchSeries(unittest.TestCase):
	def test_kraft_multilayer_initials_and_pt(self):
		item_name = "Cartón Kraft Multicapa Estucado 18pt"

		self.assertEqual(extract_initials(item_name), "CKME")
		self.assertEqual(extract_pt(item_name), "18")
		self.assertEqual(
			build_batch_number_series(item_name, 277),
			".YY.MM.DD.-CKME-18-277-.##.",
		)

	def test_solid_bleached_c1s_keeps_code_and_drops_parenthetical(self):
		item_name = "Cartón Blanco Sólido Estucado C1S (1 Cara) 28pt"

		self.assertEqual(extract_initials(item_name), "CBSEC1S")
		self.assertEqual(extract_pt(item_name), "28")
		self.assertEqual(
			build_batch_number_series(item_name, 301),
			".YY.MM.DD.-CBSEC1S-28-301-.##.",
		)

	def test_c2s_code_is_kept(self):
		item_name = "Cartón Blanco Multicapa Estucado C2S (2 Caras) 12pt"

		self.assertEqual(extract_initials(item_name), "CBMEC2S")
		self.assertEqual(extract_pt(item_name), "12")

	def test_existing_roll_sku_series(self):
		item_name = "Cartón Kraft Multicapa Estucado 20pt"

		self.assertEqual(
			build_batch_number_series(item_name, 322),
			".YY.MM.DD.-CKME-20-322-.##.",
		)

	def test_missing_pt_raises(self):
		with self.assertRaises(ValueError) as ctx:
			extract_pt("Papel Bond 20lb")

		self.assertEqual(str(ctx.exception), "pt")

	def test_missing_gsm_raises(self):
		with self.assertRaises(ValueError) as ctx:
			build_batch_number_series("Cartón Kraft Multicapa Estucado 18pt", 0)

		self.assertEqual(str(ctx.exception), "gsm")


if __name__ == "__main__":
	unittest.main()
