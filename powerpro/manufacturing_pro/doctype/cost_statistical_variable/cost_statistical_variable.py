# Copyright (c) 2024, Yefri Tavarez and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CostStatisticalVariable(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		formula: DF.Code | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		variable_name: DF.Data | None
	# end: auto-generated types
	pass
