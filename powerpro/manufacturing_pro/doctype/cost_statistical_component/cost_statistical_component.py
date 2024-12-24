# Copyright (c) 2024, Yefri Tavarez and contributors
# For license information, please see license.txt

import frappe

from frappe.utils.safe_exec import (
	# FrappeTransformer,
	# get_keys_for_autocomplete,
	# get_safe_globals,
	is_safe_exec_enabled,
	safe_exec,
)
from frappe.model.document import Document


class CostStatisticalComponent(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from powerpro.manufacturing_pro.doctype.cost_statistical_variable.cost_statistical_variable import CostStatisticalVariable

		component_name: DF.Data
		formula: DF.Code | None
		variables: DF.Table[CostStatisticalVariable]
	# end: auto-generated types
	
	def validate(self):
		if self.formula:
			self.validate_formula(self.formula)

		if self.variables:
			self.validate_variables()
	
	def validate_formula(self, formula):
		if is_safe_exec_enabled():
			try:
				safe_exec(formula, self.get_safe_globals())
			except Exception as e:
				frappe.throw(str(e))
		else:
			frappe.throw("Safe Execution is disabled")
	
	def validate_variables(self):
		for variable in self.variables:
			if variable.formula:
				try:
					self.validate_formula(variable.formula)
				except Exception as e:
					index = variable.idx
					varname = variable.variable_name

					frappe.throw(f"Error in formula for variable {varname} at row {index}: {str(e)}")

	def get_safe_globals(self):
		return {
			"frappe": frappe,
			"doc": self,
			"self": frappe._dict(),
		}
		