# Copyright (c) 2025, Yefri Tavarez and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class ProjectDocFields(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		fieldname: DF.Data | None
		hidden: DF.Check
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		read_only: DF.Check
		reqd: DF.Check
	# end: auto-generated types
	pass
