# Copyright (c) 2024, Miguel Higuera and Contributors
# For license information, please see license.txt

from collections import defaultdict

import frappe

from frappe import _
from frappe.utils import flt
from frappe.desk.reportview import get_match_cond
from hrms.payroll.doctype.payroll_entry import payroll_entry

from powerpro.controllers.salary_slip.helper import LEGACY_EMPLOYER_COMPONENTS
from powerpro.payroll_rules.employer_contributions import DEDICATED_MODE


class PayrollEntry(payroll_entry.PayrollEntry):
    def get_payable_amount_for_earnings_and_deductions(
        self,
        accounts,
        earnings,
        deductions,
        currencies,
        company_currency,
        accounting_dimensions,
        precision,
        payable_amount,
    ):
        payable_amount = super().get_payable_amount_for_earnings_and_deductions(
            accounts,
            earnings,
            deductions,
            currencies,
            company_currency,
            accounting_dimensions,
            precision,
            payable_amount,
        )
        debits, credits = self._get_dedicated_employer_contribution_totals()

        for (account, cost_center), amount in debits.items():
            payable_amount = self.get_accounting_entries_and_payable_amount(
                account,
                cost_center or self.cost_center,
                amount,
                currencies,
                company_currency,
                payable_amount,
                accounting_dimensions,
                precision,
                entry_type="debit",
                accounts=accounts,
            )

        for (account, cost_center), amount in credits.items():
            payable_amount = self.get_accounting_entries_and_payable_amount(
                account,
                cost_center or self.cost_center,
                amount,
                currencies,
                company_currency,
                payable_amount,
                accounting_dimensions,
                precision,
                entry_type="credit",
                accounts=accounts,
            )

        return payable_amount

    def _get_dedicated_employer_contribution_totals(self):
        slip_names = [row.name for row in self.get_sal_slip_list(ss_status=1, as_dict=True)]
        if not slip_names:
            return {}, {}

        slips = [frappe.get_doc("Salary Slip", name) for name in slip_names]
        dedicated_slips = [
            slip for slip in slips if slip.get("employer_contribution_mode") == DEDICATED_MODE
        ]
        if not dedicated_slips:
            return {}, {}
        if len(dedicated_slips) != len(slips):
            frappe.throw(
                _("Payroll Entry {0} mixes legacy and dedicated employer contribution modes.").format(
                    self.name
                )
            )

        debits = defaultdict(float)
        credits = defaultdict(float)
        for slip in dedicated_slips:
            legacy_rows = [
                row.salary_component
                for table in ("earnings", "deductions")
                for row in slip.get(table, [])
                if row.salary_component in LEGACY_EMPLOYER_COMPONENTS and flt(row.amount)
            ]
            if legacy_rows:
                frappe.throw(
                    _("Salary Slip {0} contains both dedicated and legacy employer contributions.").format(
                        slip.name
                    )
                )
            contribution_count = len(slip.get("employer_contributions", []))
            monthly_settlement = bool(
                slip.get("mid_month_start") or slip.payroll_frequency == "Monthly"
            )
            if monthly_settlement and contribution_count != 4:
                frappe.throw(
                    _("Salary Slip {0} does not contain four employer contribution snapshots.").format(
                        slip.name
                    )
                )
            if not monthly_settlement and contribution_count:
                frappe.throw(
                    _("Salary Slip {0} has employer contributions outside the monthly settlement.").format(
                        slip.name
                    )
                )

            cost_centers = self.get_payroll_cost_centers_for_employee(
                slip.employee, slip.salary_structure
            )
            for contribution in slip.employer_contributions:
                for cost_center, percentage in cost_centers.items():
                    amount = flt(contribution.amount) * flt(percentage) / 100
                    debits[(contribution.expense_account, cost_center)] += amount
                    credits[(contribution.payable_account, cost_center)] += amount

        return dict(debits), dict(credits)

    # @disabled
    def __make_filters(self):
        filters = frappe._dict(
            company=self.company,
            branch=self.branch,
            department=self.department,
            designation=self.designation,
            grade=self.grade,
            currency=self.currency,
            start_date=self.start_date,
            end_date=self.end_date,
            payroll_payable_account=self.payroll_payable_account,
            salary_slip_based_on_timesheet=self.salary_slip_based_on_timesheet,
            payroll_frequency=self.payroll_frequency,
        )

        # if not self.salary_slip_based_on_timesheet:
        # 	filters.update(dict(payroll_frequency=self.payroll_frequency))

        return filters

    @frappe.whitelist()
    def fill_employee_details(self):
        filters = self.make_filters()
        employees = get_employee_list(filters=filters, as_dict=True, ignore_match_conditions=True)
        self.set("employees", [])

        if not employees:
            error_msg = _(
                "No employees found for the mentioned criteria:<br>Company: {0}<br> Currency: {1}<br>Payroll Payable Account: {2}"
            ).format(
                frappe.bold(self.company),
                frappe.bold(self.currency),
                frappe.bold(self.payroll_payable_account),
            )
            if self.branch:
                error_msg += "<br>" + _("Branch: {0}").format(frappe.bold(self.branch))
            if self.department:
                error_msg += "<br>" + _("Department: {0}").format(frappe.bold(self.department))
            if self.designation:
                error_msg += "<br>" + _("Designation: {0}").format(frappe.bold(self.designation))
            if self.start_date:
                error_msg += "<br>" + _("Start date: {0}").format(frappe.bold(self.start_date))
            if self.end_date:
                error_msg += "<br>" + _("End date: {0}").format(frappe.bold(self.end_date))
            frappe.throw(error_msg, title=_("No employees found"))

        self.set("employees", employees)
        self.number_of_employees = len(self.employees)
        self.update_employees_with_withheld_salaries()

        return self.get_employees_with_unmarked_attendance()



def get_employee_list(
    filters: frappe._dict,
    searchfield=None,
    search_string=None,
    fields: list[str] | None = None,
    as_dict=True,
    limit=None,
    offset=None,
    ignore_match_conditions=False,
) -> list:
    sal_struct = get_salary_structure(
        filters.company,
        filters.currency,
        filters.salary_slip_based_on_timesheet,
        filters.payroll_frequency,
    )

    if not sal_struct:
        return []

    emp_list = get_filtered_employees(
        sal_struct,
        filters,
        searchfield,
        search_string,
        fields,
        as_dict=as_dict,
        limit=limit,
        offset=offset,
        ignore_match_conditions=ignore_match_conditions,
    )

    if as_dict:
        employees_to_check = {emp.employee: emp for emp in emp_list}
    else:
        employees_to_check = {emp[0]: emp for emp in emp_list}

    return remove_payrolled_employees(employees_to_check, filters.start_date, filters.end_date)


def get_salary_structure(
    company: str, currency: str, salary_slip_based_on_timesheet: int, payroll_frequency: str
) -> list[str]:
    SalaryStructure = frappe.qb.DocType("Salary Structure")

    query = (
        frappe.qb.from_(SalaryStructure)
        .select(SalaryStructure.name)
        .where(
            (SalaryStructure.docstatus == 1)
            & (SalaryStructure.is_active == "Yes")
            & (SalaryStructure.company == company)
            & (SalaryStructure.currency == currency)
            # Modificación para incluir la condición AND
            & (SalaryStructure.salary_slip_based_on_timesheet == salary_slip_based_on_timesheet)
            & (SalaryStructure.payroll_frequency == payroll_frequency)
        )
    )

    return query.run(pluck=True)


def get_filtered_employees(
    sal_struct,
    filters,
    searchfield=None,
    search_string=None,
    fields=None,
    as_dict=False,
    limit=None,
    offset=None,
    ignore_match_conditions=False,
) -> list:
    SalaryStructureAssignment = frappe.qb.DocType("Salary Structure Assignment")
    Employee = frappe.qb.DocType("Employee")

    query = (
        frappe.qb.from_(Employee)
        .join(SalaryStructureAssignment)
        .on(Employee.name == SalaryStructureAssignment.employee)
        .where(
            (SalaryStructureAssignment.docstatus == 1)
            & (Employee.status != "Inactive")
            & (Employee.company == filters.company)
            & ((Employee.date_of_joining <= filters.end_date) | (Employee.date_of_joining.isnull()))
            & ((Employee.relieving_date >= filters.start_date) | (Employee.relieving_date.isnull()))
            & (SalaryStructureAssignment.salary_structure.isin(sal_struct))
            & (SalaryStructureAssignment.payroll_payable_account == filters.payroll_payable_account)
            & (filters.end_date >= SalaryStructureAssignment.from_date)
        )
    )

    query = set_fields_to_select(query, fields)
    query = set_searchfield(query, searchfield, search_string, qb_object=Employee)
    query = set_filter_conditions(query, filters, qb_object=Employee)

    if not ignore_match_conditions:
        query = set_match_conditions(query=query, qb_object=Employee)

    if limit:
        query = query.limit(limit)

    if offset:
        query = query.offset(offset)

    return query.run(as_dict=as_dict)


def remove_payrolled_employees(emp_list, start_date, end_date):
    SalarySlip = frappe.qb.DocType("Salary Slip")

    employees_with_payroll = (
        frappe.qb.from_(SalarySlip)
        .select(SalarySlip.employee)
        .where(
            (SalarySlip.docstatus == 1)
            & (SalarySlip.start_date == start_date)
            & (SalarySlip.end_date == end_date)
        )
    ).run(pluck=True)

    return [emp_list[emp] for emp in emp_list if emp not in employees_with_payroll]



def set_fields_to_select(query, fields: list[str] | None = None):
    default_fields = ["employee", "employee_name", "department", "designation"]

    if fields:
        query = query.select(*fields).distinct()
    else:
        query = query.select(*default_fields).distinct()

    return query


def set_searchfield(query, searchfield, search_string, qb_object):
    if searchfield:
        query = query.where(
            (qb_object[searchfield].like("%" + search_string + "%"))
            | (qb_object.employee_name.like("%" + search_string + "%"))
        )

    return query


def set_filter_conditions(query, filters, qb_object):
    """Append optional filters to employee query"""
    if filters.get("employees"):
        query = query.where(qb_object.name.notin(filters.get("employees")))

    for fltr_key in ["branch", "department", "designation", "grade"]:
        if filters.get(fltr_key):
            query = query.where(qb_object[fltr_key] == filters[fltr_key])

    return query


def set_match_conditions(query, qb_object):
    match_conditions = get_match_cond("Employee", as_condition=False)

    for cond in match_conditions:
        if isinstance(cond, dict):
            for key, value in cond.items():
                if isinstance(value, list):
                    query = query.where(qb_object[key].isin(value))
                else:
                    query = query.where(qb_object[key] == value)

    return query
