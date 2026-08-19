# Copyright (c) 2026, PowerPro contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_datetime, getdate, now_datetime


class OvertimeAuthorization(Document):
	def before_insert(self):
		self.requested_by = frappe.session.user

	def validate(self):
		self._validate_feature_flag()
		if not self.employee or not self.work_date:
			frappe.throw(_("Employee and Work Date are required."))
		self._set_employee_snapshot()
		self._set_holiday_list()
		self._set_schedule_classification()
		self._validate_window()
		self._validate_no_overlap()
		if self.docstatus == 0:
			self.status = "Draft"

	def before_submit(self):
		if get_datetime(self.authorization_start) <= now_datetime():
			frappe.throw(
				_("Overtime must be approved before the authorized work begins."),
				title=_("Retroactive approval is not allowed"),
			)

		roles = set(frappe.get_roles())
		if self.approver and self.approver != frappe.session.user and "System Manager" not in roles:
			frappe.throw(
				_("Only the assigned approver {0} may submit this authorization.").format(
					frappe.bold(self.approver)
				),
				frappe.PermissionError,
			)

		self.status = "Approved"
		self.approved_by = frappe.session.user
		self.approved_on = now_datetime()

	def on_cancel(self):
		self.status = "Cancelled"

	def _validate_feature_flag(self):
		if not frappe.db.get_single_value(
			"DGII Payroll Settings", "enable_overtime_authorization"
		):
			frappe.throw(
				_("Overtime Authorization is disabled in DGII Payroll Settings."),
				title=_("Feature disabled"),
			)

	def _set_employee_snapshot(self):
		fields = [
			"employee_name",
			"company",
			"department",
			"designation",
			"default_shift",
			"holiday_list",
			"status",
			"overtime_eligible",
			"overtime_approver",
		]
		employee = frappe.db.get_value("Employee", self.employee, fields, as_dict=True)
		if not employee:
			frappe.throw(_("Employee {0} does not exist.").format(frappe.bold(self.employee)))
		if employee.status != "Active":
			frappe.throw(_("Only active employees can receive overtime authorization."))
		if not employee.overtime_eligible:
			frappe.throw(
				_("Employee {0} is not marked as overtime-eligible.").format(
					frappe.bold(employee.employee_name)
				)
			)

		self.employee_name = employee.employee_name
		self.company = employee.company
		self.department = employee.department
		self.designation = employee.designation
		self.shift_assignment, self.shift_type = self._resolve_shift(
			employee.default_shift
		)
		self.approver = self.approver or employee.overtime_approver
		self._employee_holiday_list = employee.holiday_list
		if not self.shift_type:
			frappe.throw(_("Employee {0} has no Shift Type.").format(frappe.bold(self.employee)))
		self._validate_approver()

	def _resolve_shift(self, default_shift):
		if not frappe.db.exists("DocType", "Shift Assignment"):
			return None, default_shift
		meta = frappe.get_meta("Shift Assignment")
		fields = ["name", "shift_type", "start_date"]
		for fieldname in ("end_date",):
			if meta.has_field(fieldname):
				fields.append(fieldname)
		assignments = frappe.get_all(
			"Shift Assignment",
			filters={
				"employee": self.employee,
				"docstatus": 1,
				"start_date": ["<=", self.work_date],
			},
			fields=fields,
			order_by="start_date desc, creation desc",
		)
		work_date = getdate(self.work_date)
		for assignment in assignments:
			if assignment.get("end_date") and getdate(assignment.end_date) < work_date:
				continue
			return assignment.name, assignment.shift_type
		return None, default_shift

	def _validate_approver(self):
		if not self.approver:
			frappe.throw(
				_("Employee {0} has no Overtime Approver configured.").format(
					frappe.bold(self.employee)
				)
			)
		if not frappe.db.get_value("User", self.approver, "enabled"):
			frappe.throw(_("The selected overtime approver is not an enabled User."))
		approval_roles = {"HR Manager", "Manufacturing Manager", "System Manager"}
		if not approval_roles.intersection(frappe.get_roles(self.approver)):
			frappe.throw(
				_("The selected approver must have HR Manager, Manufacturing Manager, or System Manager role.")
			)

	def _set_holiday_list(self):
		shift_holiday_list = frappe.db.get_value("Shift Type", self.shift_type, "holiday_list")
		company_holiday_list = frappe.db.get_value(
			"Company", self.company, "default_holiday_list"
		)
		self.holiday_list = (
			shift_holiday_list or self._employee_holiday_list or company_holiday_list
		)

	def _set_schedule_classification(self):
		from powerpro.controllers.overtime import get_schedule_context

		context = get_schedule_context(
			self.work_date, self.shift_type, self.holiday_list
		)
		if not context["holiday_list_covers_work_date"]:
			frappe.throw(
				_("Holiday List {0} does not cover Work Date {1}.").format(
					frappe.bold(self.holiday_list or _("Not set")),
					frappe.bold(self.work_date),
				)
			)
		self.day_classification = context["classification"]
		self.legal_holiday_description = "; ".join(
			context["holiday_descriptions"]
		)

	def _validate_window(self):
		if not self.authorization_start or not self.authorization_end:
			frappe.throw(_("Authorization Start and Authorization End are required."))
		start = get_datetime(self.authorization_start)
		end = get_datetime(self.authorization_end)
		if end <= start:
			frappe.throw(_("Authorization End must be after Authorization Start."))
		if getdate(start) != getdate(self.work_date):
			frappe.throw(_("Work Date must match the date of Authorization Start."))
		window_hours = (end - start).total_seconds() / 3600
		if flt(self.maximum_hours) <= 0:
			frappe.throw(_("Maximum Authorized Hours must be greater than zero."))
		if flt(self.maximum_hours) > window_hours:
			frappe.throw(
				_("Maximum Authorized Hours cannot exceed the approved time window ({0} hours).").format(
					frappe.bold(round(window_hours, 2))
				)
			)

	def _validate_no_overlap(self):
		filters = [
			["Overtime Authorization", "employee", "=", self.employee],
			["Overtime Authorization", "docstatus", "<", 2],
			["Overtime Authorization", "authorization_start", "<", self.authorization_end],
			["Overtime Authorization", "authorization_end", ">", self.authorization_start],
		]
		overlaps = frappe.get_all("Overtime Authorization", filters=filters, pluck="name")
		overlaps = [name for name in overlaps if name != self.name]
		if overlaps:
			frappe.throw(
				_("This window overlaps Overtime Authorization {0}.").format(
					frappe.bold(overlaps[0])
				)
			)
