# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


def execute():
	dstr = """CABLMUES12-00001	CA12-00001
	PACO100BR-00001	PACO10BR-00001
	CABLSOES-00001	CABLSOES-00002
	CABLSOES20-00001	CA20-00002
	CABLMUES18-00001	CA18-00003
	CABLSOES16-00001	CA16-00001
	CABLSOES-00002	CA12-00002
	CABLMUES20-00001	CA20-00001
	CABLSOES14-00001	CA14-00002
	PACO115BR-00001	PACO11BR-00001
	PAADBR-00001	PAADBR-00003
	CABLSOES12-00001	CABLSOES-00001
	CABLMUES16-00001	CA16-00002
	CABLMUES14-00001	CA14-00001
	CABLSOES18-00001	CA18-00002"""


	skus = load_skus()

	for new, old in [d.split("\t") for d in dstr.split("\n")]:
		res = do_lookup(old, skus)

		if res:
			do_replacement(old, new, res, skus)


def load_skus() -> Dict[str, Dict[str, Any]]:
	out = {}

	res = frappe.get_all("Item", fields=["name", "product_details"])
	for row in res:
		if product_details := row["product_details"]:
			out[row["name"]] = product_details

	return out


def do_lookup(material_id: str, skus: Dict[str, Dict[str, Any]]) -> bool:
	for key, value in skus.items():
		if material_id in value:
			return key

	return None


def do_replacement(old_material_id: str, new_material_id: str, sku: str, skus: Dict[str, Dict[str, Any]]) -> bool:
	"""Replace old material id with new material id in the given sku."""
	if sku not in skus:
		return False

	product_details = skus[sku]
	if old_material_id not in product_details:
		return False

	d = frappe.parse_json(product_details)
	if material := d["material"]:
		if material == old_material_id:
			d["material"] = new_material_id
			product_details = frappe.as_json(d)
			frappe.db.set_value("Item", sku, "product_details", product_details)

			print(f"Doing replacement for {sku} from {old_material_id} to {new_material_id}")
			return True
	
	return False