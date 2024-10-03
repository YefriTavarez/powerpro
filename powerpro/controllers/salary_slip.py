# Copyright (c) 2024, Miguel Higuera and Contributors
# For license information, please see license.txt

import frappe

from frappe import _
from frappe.utils import flt
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip


class SalarySlip(SalarySlip):
    def set_dgii_payroll_settings(self):
        self.dgii_payroll_settings = self.get_dgii_payroll_settings()
        self.update({
            "weekly_expected_hours": self.dgii_payroll_settings.weekly_expected_hours,
            "max_weekly_extra_hours": self.dgii_payroll_settings.max_weekly_extra_hours,
            "start_night_hours": self.dgii_payroll_settings.start_night_hours,
            "end_night_hours": self.dgii_payroll_settings.end_night_hours,
            "extra_hours_rate": self.dgii_payroll_settings.extra_hours_rate,
            "extraordinary_hours_rate": self.dgii_payroll_settings.extraordinary_hours_rate,
            "night_hours_rate": self.dgii_payroll_settings.night_hours_rate,
            "pension_fund_provider": self.dgii_payroll_settings.pension_fund_provider,
            "health_insurance_rate": self.dgii_payroll_settings.health_insurance_rate,
        })

    def get_dgii_payroll_settings(self):
        doctype = "DGII Payroll Settings"
        return frappe.get_single(doctype)

    def pull_sal_struct(self):
        from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip

        if self.salary_slip_based_on_timesheet:
            self.salary_structure = self._salary_structure_doc.name
            self.hour_rate = self._salary_structure_doc.hour_rate
            self.base_hour_rate = flt(self.hour_rate) * flt(self.exchange_rate)
            self.total_working_hours = sum([d.working_hours or 0.0 for d in self.timesheets]) or 0.0
            self.total_extra_hours = sum([d.extra_hours or 0.0 for d in self.timesheets]) or 0.0
            self.total_extraordinary_hours = sum([d.extraordinary_hours or 0.0 for d in self.timesheets]) or 0.0
            self.total_night_hours = sum([d.night_hours or 0.0 for d in self.timesheets]) or 0.0
            wages_amount = self.hour_rate * self.total_working_hours

            # self.add_earning_for_hourly_wages(self, self._salary_structure_doc.salary_component, wages_amount)

        make_salary_slip(self._salary_structure_doc.name, self)

    def set_time_sheet(self):
        self.set("timesheets", [])

        Timesheet = frappe.qb.DocType("Timesheet")
        timesheets = (
            frappe.qb.from_(Timesheet)
            .select(Timesheet.star)
            .where(
                (Timesheet.employee == self.employee)
                & (Timesheet.start_date.between(self.start_date, self.end_date))
                & ((Timesheet.status == "Submitted") | (Timesheet.status == "Billed"))
            )
        ).run(as_dict=1)

        for data in timesheets:
            self.append("timesheets", {
                "time_sheet": data.name, 
                "working_hours": data.total_hours,
                "extra_hours": data.extra_hours,
                "extraordinary_hours": data.extraordinary_hours,
                "night_hours": data.night_hours,
            })
        
        self.set_dgii_payroll_settings()


@frappe.whitelist()
def make_salary_slip_from_timesheet(source_name, target_doc=None):
    target = frappe.new_doc("Salary Slip")
    set_missing_values(source_name, target)
    target.run_method("get_emp_and_working_day_details")

    return target


def set_missing_values(time_sheet, target):
    doc = frappe.get_doc("Timesheet", time_sheet)
    target.employee = doc.employee
    target.employee_name = doc.employee_name
    target.salary_slip_based_on_timesheet = 1
    target.start_date = doc.start_date
    target.end_date = doc.end_date
    target.posting_date = doc.modified
    target.total_working_hours = doc.total_hours
    target.append("timesheets", {
            "time_sheet": doc.name, 
            "working_hours": doc.total_hours,
            "extra_hours": doc.extra_hours,
            "extraordinary_hours": doc.extraordinary_hours,
            "night_hours": doc.night_hours,
        })


