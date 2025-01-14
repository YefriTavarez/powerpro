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
		cost_structure: DF.Link
		cost_structure_assignment: DF.Link
		currency: DF.Link
		exchange_rate: DF.Float
		net_amount: DF.Currency
		operation: DF.Link
		posting_date: DF.Date
		workstation: DF.Link
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

		if self.salary_slip_based_on_timesheet:
			self.cost_structure = self._cost_structure_doc.name
			self.hour_rate = self._cost_structure_doc.hour_rate
			self.base_hour_rate = flt(self.hour_rate) * flt(self.exchange_rate)
			self.total_working_hours = sum([d.working_hours or 0.0 for d in self.timesheets]) or 0.0

		make_cost_slip(self._cost_structure_doc.name, self)

	def calculate_lwp_or_ppl_based_on_leave_application(
		self, holidays, working_days_list, daily_wages_fraction_for_half_day
	):
		lwp = 0
		leaves = get_lwp_or_ppl_for_date_range(
			self.operation,
			self.start_date,
			self.end_date,
		)

		for d in working_days_list:
			if self.relieving_date and d > self.relieving_date:
				continue

			leave = leaves.get(d)

			if not leave:
				continue

			if not leave.include_holiday and getdate(d) in holidays:
				continue

			equivalent_lwp_count = 0
			fraction_of_daily_salary_per_leave = flt(leave.fraction_of_daily_salary_per_leave)

			is_half_day_leave = False
			if cint(leave.half_day) and (leave.half_day_date == d or leave.from_date == leave.to_date):
				is_half_day_leave = True

			equivalent_lwp_count = (1 - daily_wages_fraction_for_half_day) if is_half_day_leave else 1

			if cint(leave.is_ppl):
				equivalent_lwp_count *= (
					fraction_of_daily_salary_per_leave if fraction_of_daily_salary_per_leave else 1
				)

			lwp += equivalent_lwp_count

		return lwp

	def get_leave_type_map(self) -> dict:
		"""Returns (partially paid leaves/leave without pay) leave types by name"""

		def _get_leave_type_map():
			leave_types = frappe.get_all(
				"Leave Type",
				or_filters={"is_ppl": 1, "is_lwp": 1},
				fields=["name", "is_lwp", "is_ppl", "fraction_of_daily_salary_per_leave", "include_holiday"],
			)
			return {leave_type.name: leave_type for leave_type in leave_types}

		return frappe.cache().get_value(LEAVE_TYPE_MAP, _get_leave_type_map)

	def get_employee_attendance(self, start_date, end_date):
		attendance = frappe.qb.DocType("Attendance")

		attendance_details = (
			frappe.qb.from_(attendance)
			.select(attendance.attendance_date, attendance.status, attendance.leave_type)
			.where(
				(attendance.status.isin(["Absent", "Half Day", "On Leave"]))
				& (attendance.operation == self.operation)
				& (attendance.docstatus == 1)
				& (attendance.attendance_date.between(start_date, end_date))
			)
		).run(as_dict=1)

		return attendance_details

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
		self.set_net_total_in_words()


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

		self.update_component_amount_based_on_payment_days(component_row, remove_if_zero_valued)

		if data:
			data[component_row.abbr] = component_row.amount

	def update_component_amount_based_on_payment_days(self, component_row, remove_if_zero_valued=None):
		component_row.amount = self.get_amount_based_on_payment_days(component_row)[0]

		# remove 0 valued components that have been updated later
		if component_row.amount == 0 and remove_if_zero_valued:
			self.remove(component_row)

	def set_precision_for_component_amounts(self):
		for component_type in ("components",):
			for component_row in self.get(component_type):
				component_row.amount = flt(component_row.amount, component_row.precision("amount"))

	def calculate_variable_based_on_taxable_salary(self, tax_component):
		if not self.payroll_period:
			frappe.msgprint(
				_("Start and end dates not in a valid Payroll Period, cannot calculate {0}.").format(
					tax_component
				)
			)
			return

		return self.calculate_variable_tax(tax_component)

	def calculate_variable_tax(self, tax_component):
		self.previous_total_paid_taxes = self.get_tax_paid_in_period(
			self.payroll_period.start_date, self.start_date, tax_component
		)

		# Structured tax amount
		eval_locals, default_data = self.get_data_for_eval()
		self.total_structured_tax_amount = calculate_tax_by_tax_slab(
			self.total_taxable_earnings_without_full_tax_addl_components,
			self.tax_slab,
			self.whitelisted_globals,
			eval_locals,
		)

		self.current_structured_tax_amount = (
			self.total_structured_tax_amount - self.previous_total_paid_taxes
		) / self.remaining_sub_periods

		# Total taxable earnings with additional earnings with full tax
		self.full_tax_on_additional_earnings = 0.0
		if self.current_additional_earnings_with_full_tax:
			self.total_tax_amount = calculate_tax_by_tax_slab(
				self.total_taxable_earnings, self.tax_slab, self.whitelisted_globals, eval_locals
			)
			self.full_tax_on_additional_earnings = self.total_tax_amount - self.total_structured_tax_amount

		current_tax_amount = self.current_structured_tax_amount + self.full_tax_on_additional_earnings
		if flt(current_tax_amount) < 0:
			current_tax_amount = 0

		self._component_based_variable_tax[tax_component].update(
			{
				"previous_total_paid_taxes": self.previous_total_paid_taxes,
				"total_structured_tax_amount": self.total_structured_tax_amount,
				"current_structured_tax_amount": self.current_structured_tax_amount,
				"full_tax_on_additional_earnings": self.full_tax_on_additional_earnings,
				"current_tax_amount": current_tax_amount,
			}
		)

		return current_tax_amount


	def get_taxable_earnings_for_prev_period(self, start_date, end_date, allow_tax_exemption=False):
		exempted_amount = 0
		taxable_earnings = self.get_salary_slip_details(
			start_date, end_date, parentfield="earnings", is_tax_applicable=1
		)

		if allow_tax_exemption:
			exempted_amount = self.get_salary_slip_details(
				start_date, end_date, parentfield="deductions", exempted_from_income_tax=1
			)

		opening_taxable_earning = self.get_opening_for("taxable_earnings_till_date", start_date, end_date)

		return (taxable_earnings + opening_taxable_earning) - exempted_amount, exempted_amount

	def get_opening_for(self, field_to_select, start_date, end_date):
		return self._cost_structure_assignment.get(field_to_select) or 0

	def get_salary_slip_details(
		self,
		start_date,
		end_date,
		parentfield,
		salary_component=None,
		is_tax_applicable=None,
		is_flexible_benefit=0,
		exempted_from_income_tax=0,
		variable_based_on_taxable_salary=0,
		field_to_select="amount",
	):
		ss = frappe.qb.DocType("Cost Slip")
		sd = frappe.qb.DocType("Cost Detail")

		if field_to_select == "amount":
			field = sd.amount
		else:
			field = sd.additional_amount

		query = (
			frappe.qb.from_(ss)
			.join(sd)
			.on(sd.parent == ss.name)
			.select(Sum(field))
			.where(sd.parentfield == parentfield)
			.where(sd.is_flexible_benefit == is_flexible_benefit)
			.where(ss.docstatus == 1)
			.where(ss.operation == self.operation)
			.where(ss.start_date.between(start_date, end_date))
			.where(ss.end_date.between(start_date, end_date))
		)

		if is_tax_applicable is not None:
			query = query.where(sd.is_tax_applicable == is_tax_applicable)

		if exempted_from_income_tax:
			query = query.where(sd.exempted_from_income_tax == exempted_from_income_tax)

		if variable_based_on_taxable_salary:
			query = query.where(sd.variable_based_on_taxable_salary == variable_based_on_taxable_salary)

		if salary_component:
			query = query.where(sd.salary_component == salary_component)

		result = query.run()

		return flt(result[0][0]) if result else 0.0

	def get_tax_paid_in_period(self, start_date, end_date, tax_component):
		# find total_tax_paid, tax paid for benefit, additional_cost
		total_tax_paid = self.get_salary_slip_details(
			start_date,
			end_date,
			parentfield="deductions",
			salary_component=tax_component,
			variable_based_on_taxable_salary=1,
		)

		tax_deducted_till_date = self.get_opening_for("tax_deducted_till_date", start_date, end_date)

		return total_tax_paid + tax_deducted_till_date

	def get_taxable_earnings(self, allow_tax_exemption=False, based_on_payment_days=0):
		taxable_earnings = 0
		additional_income = 0
		additional_income_with_full_tax = 0
		flexi_benefits = 0
		amount_exempted_from_income_tax = 0

		for earning in self.earnings:
			if based_on_payment_days:
				amount, additional_amount = self.get_amount_based_on_payment_days(earning)
			else:
				if earning.additional_amount:
					amount, additional_amount = earning.amount, earning.additional_amount
				else:
					amount, additional_amount = earning.default_amount, earning.additional_amount

			if earning.is_tax_applicable:
				if earning.is_flexible_benefit:
					flexi_benefits += amount
				else:
					taxable_earnings += amount - additional_amount
					additional_income += additional_amount

					# Get additional amount based on future recurring additional salary
					if additional_amount and earning.is_recurring_additional_cost:
						additional_income += self.get_future_recurring_additional_amount(
							earning.additional_cost, earning.additional_amount
						)  # Used earning.additional_amount to consider the amount for the full month

					if earning.deduct_full_tax_on_selected_payroll_date:
						additional_income_with_full_tax += additional_amount

		if allow_tax_exemption:
			for ded in self.deductions:
				if ded.exempted_from_income_tax:
					amount, additional_amount = ded.amount, ded.additional_amount
					if based_on_payment_days:
						amount, additional_amount = self.get_amount_based_on_payment_days(ded)

					taxable_earnings -= flt(amount - additional_amount)
					additional_income -= additional_amount
					amount_exempted_from_income_tax = flt(amount - additional_amount)

					if additional_amount and ded.is_recurring_additional_cost:
						additional_income -= self.get_future_recurring_additional_amount(
							ded.additional_cost, ded.additional_amount
						)  # Used ded.additional_amount to consider the amount for the full month

		return frappe._dict(
			{
				"taxable_earnings": taxable_earnings,
				"additional_income": additional_income,
				"amount_exempted_from_income_tax": amount_exempted_from_income_tax,
				"additional_income_with_full_tax": additional_income_with_full_tax,
				"flexi_benefits": flexi_benefits,
			}
		)

	def get_future_recurring_period(
		self,
		additional_cost,
	):
		to_date = None

		if self.relieving_date:
			to_date = self.relieving_date

		if not to_date:
			to_date = frappe.db.get_value("Additional Cost", additional_cost, "to_date", cache=True)

		# future month count excluding current
		from_date, to_date = getdate(self.start_date), getdate(to_date)

		# If recurring period end date is beyond the payroll period,
		# last day of payroll period should be considered for recurring period calculation
		if getdate(to_date) > getdate(self.payroll_period.end_date):
			to_date = getdate(self.payroll_period.end_date)

		future_recurring_period = ((to_date.year - from_date.year) * 12) + (to_date.month - from_date.month)

		return future_recurring_period

	def get_future_recurring_additional_amount(self, additional_cost, monthly_additional_amount):
		future_recurring_additional_amount = 0

		future_recurring_period = self.get_future_recurring_period(additional_cost)

		if future_recurring_period > 0:
			future_recurring_additional_amount = (
				monthly_additional_amount * future_recurring_period
			)  # Used earning.additional_amount to consider the amount for the full month
		return future_recurring_additional_amount

	def get_amount_based_on_payment_days(self, row):
		amount, additional_amount = row.amount, row.additional_amount
		amount = flt(row.default_amount) + flt(row.additional_amount)

		# apply rounding
		if frappe.db.get_value(
			"Cost Component", row.salary_component, "round_to_the_nearest_integer", cache=True
		):
			amount, additional_amount = rounded(amount or 0), rounded(additional_amount or 0)

		return amount, additional_amount

	def calculate_unclaimed_taxable_benefits(self):
		# get total sum of benefits paid
		total_benefits_paid = self.get_salary_slip_details(
			self.payroll_period.start_date,
			self.start_date,
			parentfield="earnings",
			is_tax_applicable=1,
			is_flexible_benefit=1,
		)

		# get total benefits claimed
		BenefitClaim = frappe.qb.DocType("Operation Benefit Claim")
		total_benefits_claimed = (
			frappe.qb.from_(BenefitClaim)
			.select(Sum(BenefitClaim.claimed_amount))
			.where(
				(BenefitClaim.docstatus == 1)
				& (BenefitClaim.operation == self.operation)
				& (BenefitClaim.claim_date.between(self.payroll_period.start_date, self.end_date))
			)
		).run()
		total_benefits_claimed = flt(total_benefits_claimed[0][0]) if total_benefits_claimed else 0

		unclaimed_taxable_benefits = (
			total_benefits_paid - total_benefits_claimed
		) + self.current_taxable_earnings_for_payment_days.flexi_benefits
		return unclaimed_taxable_benefits

	def get_total_exemption_amount(self):
		total_exemption_amount = 0
		if self.tax_slab.allow_tax_exemption:
			if self.deduct_tax_for_unsubmitted_tax_exemption_proof:
				exemption_proof = frappe.db.get_value(
					"Operation Tax Exemption Proof Submission",
					{"operation": self.operation, "payroll_period": self.payroll_period.name, "docstatus": 1},
					"exemption_amount",
					cache=True,
				)
				if exemption_proof:
					total_exemption_amount = exemption_proof
			else:
				declaration = frappe.db.get_value(
					"Operation Tax Exemption Declaration",
					{"operation": self.operation, "payroll_period": self.payroll_period.name, "docstatus": 1},
					"total_exemption_amount",
					cache=True,
				)
				if declaration:
					total_exemption_amount = declaration

		if self.tax_slab.standard_tax_exemption_amount:
			total_exemption_amount += flt(self.tax_slab.standard_tax_exemption_amount)

		return total_exemption_amount

	def get_income_form_other_sources(self):
		return (
			frappe.get_all(
				"Operation Other Income",
				filters={
					"operation": self.operation,
					"payroll_period": self.payroll_period.name,
					"company": self.company,
					"docstatus": 1,
				},
				fields="SUM(amount) as total_amount",
			)[0].total_amount
			or 0.0
		)

	def get_component_totals(self, component_type, depends_on_payment_days=0):
		total = 0.0
		for d in self.get(component_type):
			if not d.do_not_include_in_total:
				if depends_on_payment_days:
					amount = self.get_amount_based_on_payment_days(d)[0]
				else:
					amount = flt(d.amount, d.precision("amount"))
				total += amount
		return total

	def update_status(self, salary_slip=None):
		for data in self.timesheets:
			if data.time_sheet:
				timesheet = frappe.get_doc("Timesheet", data.time_sheet)
				timesheet.salary_slip = salary_slip
				timesheet.flags.ignore_validate_update_after_submit = True
				timesheet.set_status()
				timesheet.save()

	def set_status(self, status=None):
		"""Get and update status"""
		if not status:
			status = self.get_status()
		self.db_set("status", status)

	def process_cost_structure(self, for_preview=0):
		"""Calculate salary after salary structure details have been updated"""
		self.calculate_net_amount()

	@frappe.whitelist()
	def process_salary_based_on_working_days(self):
		self.calculate_net_amount()

	@frappe.whitelist()
	def set_totals(self):
		self.net_amount = 0.0
		if hasattr(self, "components"):
			for earning in self.components:
				self.net_amount += flt(earning.amount, earning.precision("amount"))
		
		self.set_base_totals()

	def set_base_totals(self):
		self.base_net_amount = flt(self.net_amount) * flt(self.exchange_rate)
		self.base_total_deduction = flt(self.total_deduction) * flt(self.exchange_rate)
		self.rounded_total = rounded(self.net_amount or 0)
		self.base_net_pay = flt(self.net_amount) * flt(self.exchange_rate)
		self.base_rounded_total = rounded(self.base_net_pay or 0)
		self.set_net_total_in_words()

	# calculate total working hours, earnings based on hourly wages and totals
	def calculate_total_for_salary_slip_based_on_timesheet(self):
		if self.timesheets:
			self.total_working_hours = 0
			for timesheet in self.timesheets:
				if timesheet.working_hours:
					self.total_working_hours += timesheet.working_hours

		wages_amount = self.total_working_hours * self.hour_rate
		self.base_hour_rate = flt(self.hour_rate) * flt(self.exchange_rate)
		salary_component = frappe.db.get_value(
			"Cost Structure", {"name": self.cost_structure}, "salary_component", cache=True
		)
		if self.earnings:
			for i, earning in enumerate(self.earnings):
				if earning.salary_component == salary_component:
					self.earnings[i].amount = wages_amount
				self.gross_pay += flt(self.earnings[i].amount, earning.precision("amount"))
		self.net_amount = flt(self.gross_pay) - flt(self.total_deduction)

	def compute_year_to_date(self):
		year_to_date = 0
		period_start_date, period_end_date = self.get_year_to_date_period()

		salary_slip_sum = frappe.get_list(
			"Cost Slip",
			fields=["sum(net_pay) as net_sum", "sum(gross_pay) as gross_sum"],
			filters={
				"operation": self.operation,
				"start_date": [">=", period_start_date],
				"end_date": ["<", period_end_date],
				"name": ["!=", self.name],
				"docstatus": 1,
			},
		)

		year_to_date = flt(salary_slip_sum[0].net_sum) if salary_slip_sum else 0.0
		gross_year_to_date = flt(salary_slip_sum[0].gross_sum) if salary_slip_sum else 0.0

		year_to_date += self.net_amount
		gross_year_to_date += self.gross_pay
		self.year_to_date = year_to_date
		self.gross_year_to_date = gross_year_to_date

	def compute_month_to_date(self):
		month_to_date = 0
		first_day_of_the_month = get_first_day(self.start_date)
		salary_slip_sum = frappe.get_list(
			"Cost Slip",
			fields=["sum(net_pay) as sum"],
			filters={
				"operation": self.operation,
				"start_date": [">=", first_day_of_the_month],
				"end_date": ["<", self.start_date],
				"name": ["!=", self.name],
				"docstatus": 1,
			},
		)

		month_to_date = flt(salary_slip_sum[0].sum) if salary_slip_sum else 0.0

		month_to_date += self.net_amount
		self.month_to_date = month_to_date

	def compute_component_wise_year_to_date(self):
		period_start_date, period_end_date = self.get_year_to_date_period()

		ss = frappe.qb.DocType("Cost Slip")
		sd = frappe.qb.DocType("Cost Detail")

		for key in ("earnings", "deductions"):
			for component in self.get(key):
				year_to_date = 0
				component_sum = (
					frappe.qb.from_(sd)
					.inner_join(ss)
					.on(sd.parent == ss.name)
					.select(Sum(sd.amount).as_("sum"))
					.where(
						(ss.operation == self.operation)
						& (sd.salary_component == component.salary_component)
						& (ss.start_date >= period_start_date)
						& (ss.end_date < period_end_date)
						& (ss.name != self.name)
						& (ss.docstatus == 1)
					)
				).run()

				year_to_date = flt(component_sum[0][0]) if component_sum else 0.0
				year_to_date += component.amount
				component.year_to_date = year_to_date

	def get_year_to_date_period(self):
		if self.payroll_period:
			period_start_date = self.payroll_period.start_date
			period_end_date = self.payroll_period.end_date
		else:
			# get dates based on fiscal year if no payroll period exists
			fiscal_year = get_fiscal_year(date=self.start_date, company=self.company, as_dict=1)
			period_start_date = fiscal_year.year_start_date
			period_end_date = fiscal_year.year_end_date

		return period_start_date, period_end_date

	def add_leave_balances(self):
		self.set("leave_details", [])

		if frappe.db.get_single_value("Payroll Settings", "show_leave_balances_in_salary_slip"):
			from hrms.hr.doctype.leave_application.leave_application import get_leave_details

			leave_details = get_leave_details(self.operation, self.end_date, True)

			for leave_type, leave_values in leave_details["leave_allocation"].items():
				self.append(
					"leave_details",
					{
						"leave_type": leave_type,
						"total_allocated_leaves": flt(leave_values.get("total_leaves")),
						"expired_leaves": flt(leave_values.get("expired_leaves")),
						"used_leaves": flt(leave_values.get("leaves_taken")),
						"pending_leaves": flt(leave_values.get("leaves_pending_approval")),
						"available_leaves": flt(leave_values.get("remaining_leaves")),
					},
				)


def unlink_ref_doc_from_salary_slip(doc, method=None):
	"""Unlinks accrual Journal Entry from Cost Slips on cancellation"""
	linked_ss = frappe.get_all(
		"Cost Slip", filters={"journal_entry": doc.name, "docstatus": ["<", 2]}, pluck="name"
	)

	if linked_ss:
		for ss in linked_ss:
			ss_doc = frappe.get_doc("Cost Slip", ss)
			frappe.db.set_value("Cost Slip", ss_doc.name, "journal_entry", "")


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
