# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt


from typing import Literal

# import frappe
from frappe.model import naming


def generate_material_primary_key(
	base_material: Literal[
		"Paperboard", "Paper", "Adhesive Paper", "Adhesive Vinyl"
	],
	ignore_validate: bool = False,
	include_naming_serie: bool = False,
) -> str:
	"""
	Generate a primary key for a material based on its type.

	Args:
		base_material (Literal["Paperboard", "Paper", "Adhesive Paper", "Adhesive Vinyl"]):
			The type of the base material.

		ignore_validate (bool, optional):
			Whether to ignore the validation of the base material.
			Defaults to False

		include_naming_serie (bool, optional):
			Whether to include the naming serie in the return value.
			Defaults to False

	Returns:
		str: A unique primary key string for the material.

	Raises:
		ValueError: If the base material is not one of the specified types.
	"""
	if base_material not in {
		"Paperboard",
		"Paper",
		"Adhesive Paper",
		"Adhesive Vinyl",
	} and not ignore_validate:
		raise ValueError(
			f"Invalid base material: {base_material}"
			"Should be one of 'Paperboard', 'Paper', 'Adhesive Paper', 'Adhesive Vinyl'"
		)

	serie = [ "MAT" ]

	if base_material == "Paperboard":
		serie.append("PB")
	elif base_material == "Paper":
		serie.append("PP")
	elif base_material == "Adhesive Paper":
		serie.append("AP")
	elif base_material == "Adhesive Vinyl":
		serie.append("AV")

	naming_serie = "".join(serie) + "-.#####"

	primary_key = naming.make_autoname(naming_serie)

	if include_naming_serie:
		return naming_serie, primary_key

	return primary_key
