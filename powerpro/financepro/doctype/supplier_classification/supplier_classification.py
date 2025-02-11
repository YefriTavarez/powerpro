# Copyright (c) 2025, Yefri Tavarez and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class SupplierClassification(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		supplier_classification: DF.Data | None
		supplier_type: DF.Literal["Company", "Individual", "Partnership"]
	# end: auto-generated types
	pass
