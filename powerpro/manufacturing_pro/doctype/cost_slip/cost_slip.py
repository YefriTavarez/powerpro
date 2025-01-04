# Copyright (c) 2025, Yefri Tavarez and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CostSlip(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from hrms.payroll.doctype.salary_detail.salary_detail import SalaryDetail
		from hrms.payroll.doctype.salary_slip_leave.salary_slip_leave import SalarySlipLeave
		from hrms.payroll.doctype.salary_slip_timesheet.salary_slip_timesheet import SalarySlipTimesheet

		absent_days: DF.Float
		amended_from: DF.Link | None
		annual_taxable_amount: DF.Currency
		bank_account_no: DF.Data | None
		bank_name: DF.Data | None
		base_gross_pay: DF.Currency
		base_gross_year_to_date: DF.Currency
		base_hour_rate: DF.Currency
		base_month_to_date: DF.Currency
		base_net_pay: DF.Currency
		base_rounded_total: DF.Currency
		base_total_deduction: DF.Currency
		base_total_in_words: DF.Data | None
		base_year_to_date: DF.Currency
		branch: DF.Link | None
		company: DF.Link
		ctc: DF.Currency
		currency: DF.Link
		current_month_income_tax: DF.Currency
		deduct_tax_for_unclaimed_employee_benefits: DF.Check
		deduct_tax_for_unsubmitted_tax_exemption_proof: DF.Check
		deductions: DF.Table[SalaryDetail]
		deductions_before_tax_calculation: DF.Currency
		department: DF.Link | None
		designation: DF.Link | None
		earnings: DF.Table[SalaryDetail]
		employee: DF.Link
		employee_name: DF.ReadOnly
		end_date: DF.Date | None
		exchange_rate: DF.Float
		future_income_tax_deductions: DF.Currency
		gross_pay: DF.Currency
		gross_year_to_date: DF.Currency
		hour_rate: DF.Currency
		income_from_other_sources: DF.Currency
		income_tax_deducted_till_date: DF.Currency
		journal_entry: DF.Link | None
		leave_details: DF.Table[SalarySlipLeave]
		leave_without_pay: DF.Float
		letter_head: DF.Link | None
		mode_of_payment: DF.Literal[None]
		month_to_date: DF.Currency
		net_pay: DF.Currency
		non_taxable_earnings: DF.Currency
		payment_days: DF.Float
		payroll_entry: DF.Link | None
		payroll_frequency: DF.Literal["", "Monthly", "Fortnightly", "Bimonthly", "Weekly", "Daily"]
		posting_date: DF.Date
		rounded_total: DF.Currency
		salary_slip_based_on_timesheet: DF.Check
		salary_structure: DF.Link
		salary_withholding: DF.Link | None
		salary_withholding_cycle: DF.Data | None
		standard_tax_exemption_amount: DF.Currency
		start_date: DF.Date | None
		status: DF.Literal["Draft", "Submitted", "Cancelled", "Withheld"]
		tax_exemption_declaration: DF.Currency
		timesheets: DF.Table[SalarySlipTimesheet]
		total_deduction: DF.Currency
		total_earnings: DF.Currency
		total_in_words: DF.Data | None
		total_income_tax: DF.Currency
		total_working_days: DF.Float
		total_working_hours: DF.Float
		unmarked_days: DF.Float
		year_to_date: DF.Currency
	# end: auto-generated types
	pass
