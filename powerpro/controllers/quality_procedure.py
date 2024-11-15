# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

# import frappe

from frappe.model import naming
from erpnext.quality_management.doctype.quality_procedure import quality_procedure

class QualityProcedure(quality_procedure.QualityProcedure):
	def autoname(self):
		department_prefix = self.department[:3]
		naming_series = f"PRO-CAL-{department_prefix.upper()}-.#####"
		self.name = naming.make_autoname(naming_series)

	department: str = None
	created_by: str = None
	created_on: str = None
	reviewed_by: str = None
	reviewed_on: str = None
