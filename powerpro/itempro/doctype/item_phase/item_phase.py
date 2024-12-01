# Copyright (c) 2024, Yefri Tavarez and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class ItemPhase(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.model.document import Document
		from frappe.types import DF

		item_names: DF.Table[Document]
		item_phase: DF.Data | None
	# end: auto-generated types
	pass
