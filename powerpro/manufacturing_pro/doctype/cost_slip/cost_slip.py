# Copyright (c) 2025, Yefri Tavarez and contributors
# For license information, please see license.txt

import unicodedata
from datetime import date

import frappe
from frappe import _, msgprint
from frappe.model.naming import make_autoname
from frappe.query_builder import Order
from frappe.query_builder.functions import Count, Sum
from frappe.utils import (
	add_days,
	ceil,
	cint,
	cstr,
	date_diff,
	floor,
	flt,
	formatdate,
	get_first_day,
	get_last_day,
	get_link_to_form,
	getdate,
	money_in_words,
	rounded,
)
# from frappe.utils.background_jobs import enqueue

# import erpnext
from erpnext.accounts.utils import get_fiscal_year
from erpnext.utilities.transaction_base import TransactionBase

from hrms.payroll.utils import sanitize_expression
# from hrms.utils.holiday_list import get_holiday_dates_between

# cache keys
HOLIDAYS_BETWEEN_DATES = "holidays_between_dates"
LEAVE_TYPE_MAP = "leave_type_map"
SALARY_COMPONENT_VALUES = "salary_component_values"
TAX_COMPONENTS_BY_COMPANY = "tax_components_by_company"



class CostSlip(TransactionBase):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from powerpro.manufacturing_pro.doctype.cost_detail.cost_detail import CostDetail

		amended_from: DF.Link | None
		components: DF.Table[CostDetail]
		cost_estimation: DF.Link
		cost_structure: DF.Link | None
		cost_structure_assignment: DF.Link
		net_amount: DF.Currency
		operation: DF.Link | None
		posting_date: DF.Date
		selected: DF.Check
		workstation: DF.Link | None
	# end: auto-generated types

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.series = f"COST-SLIP-.#####"
		self.whitelisted_globals = {
			"int": int,
			"float": float,
			"long": int,
			"round": round,
			"rounded": rounded,
			"date": date,
			"getdate": getdate,
			"get_first_day": get_first_day,
			"get_last_day": get_last_day,
			"ceil": ceil,
			"floor": floor,
		}

	def autoname(self):
		self.name = make_autoname(self.series)

	def validate(self):
		self.set_cost_structure_assignment()
		self.calculate_net_amount()

	def on_submit(self):
		if self.net_amount < 0:
			frappe.throw(_("Net Amount cannot be less than 0"))

	def on_trash(self):
		from frappe.model.naming import revert_series_if_last

		revert_series_if_last(self.series, self.name)

	@frappe.whitelist()
	def fetch_component_details(self):
		if not self.operation:
			frappe.throw(_("Please select Operation first"))

		self.set_cost_structure_assignment()
		self.set_salary_structure_doc()

		if self.cost_structure:
			self.pull_sal_struct()

		else:
			self.check_cost_struct()

		self.calculate_net_amount()

		return self.as_dict()

	def check_cost_struct(self):
		cs = frappe.qb.DocType("Cost Structure")
		csa = frappe.qb.DocType("Cost Structure Assignment")

		query = (
			frappe.qb.from_(csa)
			.join(cs)
			.on(csa.cost_structure == cs.name)
			.select(csa.cost_structure)
			.where(
				(csa.docstatus == 1)
				& (cs.docstatus == 1)
				& (cs.is_active == "Yes")
				& (csa.operation == self.operation)
				& (
					(csa.from_date <= self.start_date)
					| (csa.from_date <= self.end_date)
					| (csa.from_date <= self.joining_date)
				)
			)
			.orderby(csa.from_date, order=Order.desc)
			.limit(1)
		)

		if not self.salary_slip_based_on_timesheet and self.payroll_frequency:
			query = query.where(cs.payroll_frequency == self.payroll_frequency)

		st_name = query.run()

		if st_name:
			self.cost_structure = st_name[0][0]
			return self.cost_structure
		else:
			self.cost_structure = None
			frappe.msgprint(
				_("No active or default Cost Structure found for operation {0} for the given dates").format(
					self.operation
				),
				title=_("Cost Structure Missing"),
			)

	def pull_sal_struct(self):
		from powerpro.manufacturing_pro.doctype.cost_structure.cost_structure import make_cost_slip
		make_cost_slip(self._cost_structure_doc.name, self)

	def add_earning_for_hourly_wages(self, doc, salary_component, amount):
		row_exists = False
		for row in doc.components:
			if row.salary_component == salary_component:
				row.amount = amount
				row_exists = True
				break

		if not row_exists:
			wages_row = {
				"salary_component": salary_component,
				"abbr": frappe.db.get_value(
					"Cost Component", salary_component, "salary_component_abbr", cache=True
				),
				"amount": self.hour_rate * self.total_working_hours,
				"default_amount": 0.0,
				"additional_amount": 0.0,
			}
			doc.append("components", wages_row)

	def set_cost_structure_assignment(self):
		self._cost_structure_assignment = frappe.db.get_value(
			"Cost Structure Assignment",
			{
				"operation": self.operation,
				"cost_structure": self.cost_structure,
			},
			"*",
			as_dict=True,
		)

		if not self._cost_structure_assignment:
			frappe.throw(
				_(
					"Please assign a Cost Structure for Operation {0} applicable from or before {1} first"
				).format(
					frappe.bold(self.operation),
					frappe.bold(formatdate(self.posting_date)),
				)
			)

	def calculate_net_amount(self, skip_tax_breakup_computation: bool = False):
		# def set_gross_pay_and_base_gross_pay():
		# 	self.base_gross_pay = flt(
		# 		flt(self.gross_pay) * flt(self.exchange_rate), self.precision("base_gross_pay")
		# 	)

		if self.cost_structure:
			self.calculate_component_amounts("components")

		self.net_amount = self.get_component_totals("components")

		# get remaining numbers of sub-period (period for which one salary is processed)
		# if self.payroll_period:
		# 	self.remaining_sub_periods = get_period_factor(
		# 		self.operation,
		# 		self.start_date,
		# 		self.end_date,
		# 		self.payroll_frequency,
		# 		self.payroll_period,
		# 		joining_date=self.joining_date,
		# 		relieving_date=self.relieving_date,
		# 	)[1]

		# set_gross_pay_and_base_gross_pay()

		# if self.cost_structure:
			# self.calculate_component_amounts("deductions")

		# set_loan_repayment(self)

		self.set_precision_for_component_amounts()
		# self.set_net_amount()

	def set_net_amount(self):
		# self.total_deduction = self.get_component_totals("deductions")
		self.total_deduction = 0.0
		# self.base_total_deduction = flt(
		# 	flt(self.total_deduction) * flt(self.exchange_rate), self.precision("base_total_deduction")
		# )
		# self.net_amount = flt(self.gross_pay)
		self.rounded_total = rounded(self.net_amount)
		self.base_net_pay = flt(flt(self.net_amount) * flt(self.exchange_rate), self.precision("base_net_pay"))
		self.base_rounded_total = flt(rounded(self.base_net_pay), self.precision("base_net_pay"))
		if self.hour_rate:
			self.base_hour_rate = flt(
				flt(self.hour_rate) * flt(self.exchange_rate), self.precision("base_hour_rate")
			)


	def get_amount_from_formula(self, struct_row, sub_period=1):
		if self.payroll_frequency == "Monthly":
			start_date = frappe.utils.add_months(self.start_date, sub_period)
			end_date = frappe.utils.add_months(self.end_date, sub_period)
			posting_date = frappe.utils.add_months(self.posting_date, sub_period)

		else:
			days_to_add = 0
			if self.payroll_frequency == "Weekly":
				days_to_add = sub_period * 6

			if self.payroll_frequency == "Fortnightly":
				days_to_add = sub_period * 13

			if self.payroll_frequency == "Daily":
				days_to_add = start_date

			start_date = frappe.utils.add_days(self.start_date, days_to_add)
			end_date = frappe.utils.add_days(self.end_date, days_to_add)
			posting_date = start_date

		local_data = self.data.copy()
		local_data.update({"start_date": start_date, "end_date": end_date, "posting_date": posting_date})

		return flt(self.eval_condition_and_formula(struct_row, local_data))


	def calculate_component_amounts(self, component_type):
		if not getattr(self, "_cost_structure_doc", None):
			self.set_salary_structure_doc()

		self.add_structure_components(component_type)

	def set_salary_structure_doc(self) -> None:
		self._cost_structure_doc = frappe.get_cached_doc("Cost Structure", self.cost_structure)
		# sanitize condition and formula fields
		for table in ("components",):
			for row in self._cost_structure_doc.get(table):
				row.condition = sanitize_expression(row.condition)
				row.formula = sanitize_expression(row.formula)

	def add_structure_components(self, component_type):
		self.data, self.default_data = self.get_data_for_eval()

		for struct_row in self._cost_structure_doc.get(component_type):
			self.add_structure_component(struct_row, component_type)

	def add_structure_component(self, struct_row, component_type):
		if (
			struct_row.salary_component == self._cost_structure_doc.salary_component
		):
			return

		amount = self.eval_condition_and_formula(struct_row, self.data)
		if struct_row.statistical_component:
			# update statitical component amount in reference data based on payment days
			# since row for statistical component is not added to salary slip

			self.default_data[struct_row.abbr] = flt(amount)
			if struct_row.depends_on_payment_days:
				payment_days_amount = (
					flt(amount) * flt(self.payment_days) / cint(self.total_working_days)
					if self.total_working_days
					else 0
				)
				self.data[struct_row.abbr] = flt(payment_days_amount, struct_row.precision("amount"))

		else:
			# default behavior, the system does not add if component amount is zero
			# if remove_if_zero_valued is unchecked, then ask system to add component row
			remove_if_zero_valued = frappe.get_cached_value(
				"Cost Component", struct_row.salary_component, "remove_if_zero_valued"
			)

			default_amount = 0

			if (
				amount
				or (struct_row.amount_based_on_formula and amount is not None)
				or (not remove_if_zero_valued and amount is not None and not self.data[struct_row.abbr])
			):
				default_amount = self.eval_condition_and_formula(struct_row, self.default_data)
				self.update_component_row(
					struct_row,
					amount,
					component_type,
					data=self.data,
					default_amount=default_amount,
					remove_if_zero_valued=remove_if_zero_valued,
				)

	def get_data_for_eval(self):
		"""Returns data for evaluating formula"""
		data = frappe._dict()
		operation = frappe.get_cached_doc("Operation", self.operation).as_dict()

		if not hasattr(self, "_cost_structure_assignment"):
			self.set_cost_structure_assignment()

		data.update(self._cost_structure_assignment)
		data.update(self.as_dict())
		data.update(operation)

		data.update(self.get_component_abbr_map())

		# shallow copy of data to store default amounts (without payment days) for tax calculation
		default_data = data.copy()

		for key in ("components",):
			for d in self.get(key):
				default_data[d.abbr] = d.default_amount or 0
				data[d.abbr] = d.amount or 0

		return data, default_data

	def get_component_abbr_map(self):
		def _fetch_component_values():
			return {
				component_abbr: 0
				for component_abbr in frappe.get_all("Cost Component", pluck="salary_component_abbr")
			}

		return frappe.cache().get_value(SALARY_COMPONENT_VALUES, generator=_fetch_component_values)

	def eval_condition_and_formula(self, struct_row, data):
		try:
			condition, formula, amount = struct_row.condition, struct_row.formula, struct_row.amount
			if condition and not _safe_eval(condition, self.whitelisted_globals, data):
				return None
			if struct_row.amount_based_on_formula and formula:
				amount = flt(
					_safe_eval(formula, self.whitelisted_globals, data), struct_row.precision("amount")
				)
			if amount:
				data[struct_row.abbr] = amount

			return amount

		except NameError as ne:
			throw_error_message(
				struct_row,
				ne,
				title=_("Name error"),
				description=_("This error can be due to missing or deleted field."),
			)
		except SyntaxError as se:
			throw_error_message(
				struct_row,
				se,
				title=_("Syntax error"),
				description=_("This error can be due to invalid syntax."),
			)
		except Exception as exc:
			throw_error_message(
				struct_row,
				exc,
				title=_("Error in formula or condition"),
				description=_("This error can be due to invalid formula or condition."),
			)
			raise

	def update_component_row(
		self,
		component_data,
		amount,
		component_type,
		additional_cost=None,
		is_recurring=0,
		data=None,
		default_amount=None,
		remove_if_zero_valued=None,
	):
		component_row = None
		for d in self.get(component_type):
			if d.salary_component != component_data.salary_component:
				continue

			if (not d.additional_cost and (not additional_cost or additional_cost.overwrite)) or (
				additional_cost and additional_cost.name == d.additional_cost
			):
				component_row = d
				break

		if additional_cost and additional_cost.overwrite:
			# Additional Cost with overwrite checked, remove default rows of same component
			self.set(
				component_type,
				[
					d
					for d in self.get(component_type)
					if d.salary_component != component_data.salary_component
					or (d.additional_cost and additional_cost.name != d.additional_cost)
					or d == component_row
				],
			)

		if not component_row:
			if not (amount or default_amount) and remove_if_zero_valued:
				return

			component_row = self.append(component_type)
			for attr in (
				"depends_on_payment_days",
				"salary_component",
				"abbr",
				"do_not_include_in_total",
				"is_tax_applicable",
				"is_flexible_benefit",
				"variable_based_on_taxable_salary",
				"exempted_from_income_tax",
			):
				component_row.set(attr, component_data.get(attr))

		if additional_cost:
			if additional_cost.overwrite:
				component_row.additional_amount = flt(
					flt(amount) - flt(component_row.get("default_amount", 0)),
					component_row.precision("additional_amount"),
				)
			else:
				component_row.default_amount = 0
				component_row.additional_amount = amount

			component_row.is_recurring_additional_cost = is_recurring
			component_row.additional_cost = additional_cost.name
			component_row.deduct_full_tax_on_selected_payroll_date = (
				additional_cost.deduct_full_tax_on_selected_payroll_date
			)
		else:
			component_row.default_amount = default_amount or amount
			component_row.additional_amount = 0
			component_row.deduct_full_tax_on_selected_payroll_date = (
				component_data.deduct_full_tax_on_selected_payroll_date
			)

		component_row.amount = amount

		if data:
			data[component_row.abbr] = component_row.amount

	def get_component_totals(self, component_type, depends_on_payment_days=0):
		total = 0.0
		for d in self.get(component_type):
			amount = flt(d.amount, d.precision("amount"))
			total += amount
		return total

	def process_cost_structure(self, for_preview=0):
		"""Calculate salary after salary structure details have been updated"""
		self.calculate_net_amount()

	@frappe.whitelist()
	def set_totals(self):
		self.net_amount = 0.0
		if hasattr(self, "components"):
			for earning in self.components:
				self.net_amount += flt(earning.amount, earning.precision("amount"))
		
	# 	self.set_base_totals()

	# def set_base_totals(self):
	# 	self.base_net_amount = flt(self.net_amount) * flt(self.exchange_rate)
	# 	self.base_total_deduction = flt(self.total_deduction) * flt(self.exchange_rate)
	# 	self.rounded_total = rounded(self.net_amount or 0)
	# 	self.base_net_pay = flt(self.net_amount) * flt(self.exchange_rate)
	# 	self.base_rounded_total = rounded(self.base_net_pay or 0)


def generate_password_for_pdf(policy_template, operation):
	operation = frappe.get_cached_doc("Operation", operation)
	return policy_template.format(**operation.as_dict())


def get_salary_component_data(component):
	# get_cached_value doesn't work here due to alias "name as salary_component"
	return frappe.db.get_value(
		"Cost Component",
		component,
		(
			"name as salary_component",
			"depends_on_payment_days",
			"salary_component_abbr as abbr",
			"do_not_include_in_total",
			"is_tax_applicable",
			"is_flexible_benefit",
			"variable_based_on_taxable_salary",
		),
		as_dict=1,
		cache=True,
	)


def get_payroll_payable_account(company, payroll_entry):
	if payroll_entry:
		payroll_payable_account = frappe.db.get_value(
			"Payroll Entry", payroll_entry, "payroll_payable_account", cache=True
		)
	else:
		payroll_payable_account = frappe.db.get_value(
			"Company", company, "default_payroll_payable_account", cache=True
		)

	return payroll_payable_account


def calculate_tax_by_tax_slab(annual_taxable_earning, tax_slab, eval_globals=None, eval_locals=None):
	eval_locals.update({"annual_taxable_earning": annual_taxable_earning})
	tax_amount = 0
	for slab in tax_slab.slabs:
		cond = cstr(slab.condition).strip()
		if cond and not eval_tax_slab_condition(cond, eval_globals, eval_locals):
			continue
		if not slab.to_amount and annual_taxable_earning >= slab.from_amount:
			tax_amount += (annual_taxable_earning - slab.from_amount + 1) * slab.percent_deduction * 0.01
			continue

		if annual_taxable_earning >= slab.from_amount and annual_taxable_earning < slab.to_amount:
			tax_amount += (annual_taxable_earning - slab.from_amount + 1) * slab.percent_deduction * 0.01
		elif annual_taxable_earning >= slab.from_amount and annual_taxable_earning >= slab.to_amount:
			tax_amount += (slab.to_amount - slab.from_amount + 1) * slab.percent_deduction * 0.01

	# other taxes and charges on income tax
	for d in tax_slab.other_taxes_and_charges:
		if flt(d.min_taxable_income) and flt(d.min_taxable_income) > annual_taxable_earning:
			continue

		if flt(d.max_taxable_income) and flt(d.max_taxable_income) < annual_taxable_earning:
			continue

		tax_amount += tax_amount * flt(d.percent) / 100

	return tax_amount


def eval_tax_slab_condition(condition, eval_globals=None, eval_locals=None):
	if not eval_globals:
		eval_globals = {
			"int": int,
			"float": float,
			"long": int,
			"round": round,
			"date": date,
			"getdate": getdate,
			"get_first_day": get_first_day,
			"get_last_day": get_last_day,
		}

	try:
		condition = condition.strip()
		if condition:
			return frappe.safe_eval(condition, eval_globals, eval_locals)
	except NameError as err:
		frappe.throw(
			_("{0} <br> This error can be due to missing or deleted field.").format(err),
			title=_("Name error"),
		)
	except SyntaxError as err:
		frappe.throw(_("Syntax error in condition: {0} in Income Tax Slab").format(err))
	except Exception as e:
		frappe.throw(_("Error in formula or condition: {0} in Income Tax Slab").format(e))
		raise


def get_lwp_or_ppl_for_date_range(operation, start_date, end_date):
	LeaveApplication = frappe.qb.DocType("Leave Application")
	LeaveType = frappe.qb.DocType("Leave Type")

	leaves = (
		frappe.qb.from_(LeaveApplication)
		.inner_join(LeaveType)
		.on(LeaveType.name == LeaveApplication.leave_type)
		.select(
			LeaveApplication.name,
			LeaveType.is_ppl,
			LeaveType.fraction_of_daily_salary_per_leave,
			LeaveType.include_holiday,
			LeaveApplication.from_date,
			LeaveApplication.to_date,
			LeaveApplication.half_day,
			LeaveApplication.half_day_date,
		)
		.where(
			((LeaveType.is_lwp == 1) | (LeaveType.is_ppl == 1))
			& (LeaveApplication.docstatus == 1)
			& (LeaveApplication.status == "Approved")
			& (LeaveApplication.operation == operation)
			& ((LeaveApplication.salary_slip.isnull()) | (LeaveApplication.salary_slip == ""))
			& ((LeaveApplication.from_date <= end_date) & (LeaveApplication.to_date >= start_date))
		)
	).run(as_dict=True)

	leave_date_mapper = frappe._dict()
	for leave in leaves:
		if leave.from_date == leave.to_date:
			leave_date_mapper[leave.from_date] = leave
		else:
			date_diff = (getdate(leave.to_date) - getdate(leave.from_date)).days
			for i in range(date_diff + 1):
				date = add_days(leave.from_date, i)
				leave_date_mapper[date] = leave

	return leave_date_mapper


@frappe.whitelist()
def make_salary_slip_from_timesheet(source_name, target_doc=None):
	target = frappe.new_doc("Cost Slip")
	set_missing_values(source_name, target)
	target.run_method("get_emp_and_working_day_details")

	return target


def set_missing_values(time_sheet, target):
	doc = frappe.get_doc("Timesheet", time_sheet)
	target.operation = doc.operation
	target.salary_slip_based_on_timesheet = 1
	target.start_date = doc.start_date
	target.end_date = doc.end_date
	target.posting_date = doc.modified
	target.total_working_hours = doc.total_hours
	target.append("timesheets", {"time_sheet": doc.name, "working_hours": doc.total_hours})


def throw_error_message(row, error, title, description=None):
	data = frappe._dict(
		{
			"doctype": row.parenttype,
			"name": row.parent,
			"doclink": get_link_to_form(row.parenttype, row.parent),
			"row_id": row.idx,
			"error": error,
			"title": title,
			"description": description or "",
		}
	)

	message = _(
		"Error while evaluating the {doctype} {doclink} at row {row_id}. <br><br> <b>Error:</b> {error} <br><br> <b>Hint:</b> {description}"
	).format(**data)

	frappe.throw(message, title=title)


# def on_doctype_update():
# 	frappe.db.add_index("Cost Slip", ["operation", "posting_date"])


def _safe_eval(code: str, eval_globals: dict | None = None, eval_locals: dict | None = None):
	"""Old version of safe_eval from framework.

	Note: current frappe.safe_eval transforms code so if you have nested
	iterations with too much depth then it can hit recursion limit of python.
	There's no workaround for this and people need large formulas in some
	countries so this is alternate implementation for that.

	WARNING: DO NOT use this function anywhere else outside of this file.
	"""
	code = unicodedata.normalize("NFKC", code)

	_check_attributes(code)

	whitelisted_globals = {"int": int, "float": float, "long": int, "round": round}
	if not eval_globals:
		eval_globals = {}

	eval_globals["__builtins__"] = {}
	eval_globals.update(whitelisted_globals)
	return eval(code, eval_globals, eval_locals)  # nosemgrep


def _check_attributes(code: str) -> None:
	import ast

	from frappe.utils.safe_exec import UNSAFE_ATTRIBUTES

	unsafe_attrs = set(UNSAFE_ATTRIBUTES).union(["__"]) - {"format"}

	for attribute in unsafe_attrs:
		if attribute in code:
			raise SyntaxError(f'Illegal rule {frappe.bold(code)}. Cannot use "{attribute}"')

	BLOCKED_NODES = (ast.NamedExpr,)

	tree = ast.parse(code, mode="eval")
	for node in ast.walk(tree):
		if isinstance(node, BLOCKED_NODES):
			raise SyntaxError(f"Operation not allowed: line {node.lineno} column {node.col_offset}")
		if isinstance(node, ast.Attribute) and isinstance(node.attr, str) and node.attr in UNSAFE_ATTRIBUTES:
			raise SyntaxError(f'Illegal rule {frappe.bold(code)}. Cannot use "{node.attr}"')
