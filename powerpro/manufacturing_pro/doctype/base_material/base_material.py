# Copyright (c) 2024, Yefri Tavarez and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class BaseMaterial(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		base_material: DF.Data
		item_group: DF.Link | None
		option_name_1: DF.Data | None
		option_name_2: DF.Data | None
		option_name_3: DF.Data | None
		options_1: DF.SmallText | None
		options_2: DF.SmallText | None
		options_3: DF.SmallText | None
	# end: auto-generated types
	pass
