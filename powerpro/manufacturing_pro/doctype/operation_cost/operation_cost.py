# Copyright (c) 2024, Yefri Tavarez and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class OperationCost(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from powerpro.manufacturing_pro.doctype.statistical_components.statistical_components import StatisticalComponents
		from powerpro.manufacturing_pro.doctype.workstations.workstations import Workstations

		operation: DF.Link
		statistical_components: DF.TableMultiSelect[StatisticalComponents]
		workstations: DF.TableMultiSelect[Workstations]
	# end: auto-generated types
	pass
