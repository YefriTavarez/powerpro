# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import copy

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import append_number_if_name_exists

from hrms.payroll.utils import sanitize_expression


class CostComponent(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from hrms.payroll.doctype.salary_component_account.salary_component_account import SalaryComponentAccount

		accounts: DF.Table[SalaryComponentAccount]
		amount: DF.Currency
		amount_based_on_formula: DF.Check
		condition: DF.Code | None
		cost_component: DF.Data
		cost_component_abbr: DF.Data
		description: DF.SmallText | None
		disabled: DF.Check
		do_not_include_in_total: DF.Check
		formula: DF.Code | None
		round_to_the_nearest_integer: DF.Check
		statistical_component: DF.Check
		variable_based_on_taxable_salary: DF.Check
	# end: auto-generated types
	def before_validate(self):
		self._condition, self.condition = self.condition, sanitize_expression(self.condition)
		self._formula, self.formula = self.formula, sanitize_expression(self.formula)

	def validate(self):
		self.validate_abbr()
		# self.validate_accounts()

	def on_update(self):
		# set old values (allowing multiline strings for better readability in the doctype form)
		if self._condition != self.condition:
			self.db_set("condition", self._condition)
		if self._formula != self.formula:
			self.db_set("formula", self._formula)

	# def clear_cache(self):
	# 	from hrms.payroll.doctype.salary_slip.salary_slip import (
	# 		SALARY_COMPONENT_VALUES,
	# 		TAX_COMPONENTS_BY_COMPANY,
	# 	)

	# 	frappe.cache().delete_value(SALARY_COMPONENT_VALUES)
	# 	frappe.cache().delete_value(TAX_COMPONENTS_BY_COMPANY)
	# 	return super().clear_cache()

	def validate_abbr(self):
		if not self.cost_component_abbr:
			self.cost_component_abbr = "".join([c[0] for c in self.cost_component.split()]).upper()

		self.cost_component_abbr = self.cost_component_abbr.strip()
		self.cost_component_abbr = append_number_if_name_exists(
			"Cost Component",
			self.cost_component_abbr,
			"cost_component_abbr",
			separator="_",
			filters={"name": ["!=", self.name]},
		)

	# def validate_accounts(self):
	# 	if not (self.statistical_component or (self.accounts and all(d.account for d in self.accounts))):
	# 		frappe.msgprint(
	# 			title=_("Warning"),
	# 			msg=_("Accounts not set for Cost Component {0}").format(self.name),
	# 			indicator="orange",
	# 		)

	@frappe.whitelist()
	def get_structures_to_be_updated(self):
		...
		# CostStructure = frappe.qb.DocType("Cost Structure")
		# SalaryDetail = frappe.qb.DocType("Salary Detail")
		# return (
		# 	frappe.qb.from_(CostStructure)
		# 	.inner_join(SalaryDetail)
		# 	.on(CostStructure.name == SalaryDetail.parent)
		# 	.select(CostStructure.name)
		# 	.where((SalaryDetail.cost_component == self.name) & (CostStructure.docstatus != 2))
		# 	.run(pluck=True)
		# )

	@frappe.whitelist()
	def update_salary_structures(self, field, value, structures=None):
		...
		# if not structures:
		# 	structures = self.get_structures_to_be_updated()

		# for structure in structures:
		# 	salary_structure = frappe.get_doc("Cost Structure", structure)
		# 	# this is only used for versioning and we do not want
		# 	# to make separate db calls by using load_doc_before_save
		# 	# which proves to be expensive while doing bulk replace
		# 	salary_structure._doc_before_save = copy.deepcopy(salary_structure)

		# 	salary_detail_row = next(
		# 		(d for d in salary_structure.get(f"{self.type.lower()}s") if d.cost_component == self.name),
		# 		None,
		# 	)
		# 	salary_detail_row.set(field, value)
		# 	salary_structure.db_update_all()
		# 	salary_structure.flags.updater_reference = {
		# 		"doctype": self.doctype,
		# 		"docname": self.name,
		# 		"label": _("via Cost Component sync"),
		# 	}
		# 	salary_structure.save_version()
