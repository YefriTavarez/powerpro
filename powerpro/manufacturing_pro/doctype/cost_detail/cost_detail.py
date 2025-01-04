# Copyright (c) 2024, Yefri Tavarez and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CostDetail(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		abbr: DF.Data | None
		amount: DF.Currency
		amount_based_on_formula: DF.Check
		condition: DF.Code | None
		cost_component: DF.Link
		default_amount: DF.Currency
		formula: DF.Code | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		statistical_component: DF.Check
	# end: auto-generated types
	pass
