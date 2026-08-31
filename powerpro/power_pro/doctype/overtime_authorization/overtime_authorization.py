# Copyright (c) 2026, PowerPro contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_datetime, getdate, now_datetime


def apply_employee_approver_snapshot(authorization, employee):
	"""Make the Employee assignment authoritative over any client-supplied value."""
	authorization.approver = employee.overtime_approver


def is_assigned_approver(assigned_approver, acting_user):
	return bool(assigned_approver) and assigned_approver == acting_user


def apply_requester_snapshot(authorization, acting_user):
	"""Keep the immutable document owner authoritative for the request audit."""
	authorization.requested_by = authorization.owner or acting_user


class OvertimeAuthorization(Document):
	def before_insert(self):
		apply_requester_snapshot(self, frappe.session.user)

	def validate(self):
		self._validate_feature_flag()
		apply_requester_snapshot(self, frappe.session.user)
		if not self.employee or not self.work_date:
			frappe.throw(_("Employee and Work Date are required."))
		self._set_employee_snapshot()
		self._set_holiday_list()
		self._set_schedule_classification()
		self._validate_window()
		self._validate_work_call_source()
		self._validate_no_overlap()
		if self.docstatus == 0:
			self.status = "Draft"

	def before_submit(self):
		if get_datetime(self.authorization_start) <= now_datetime():
			frappe.throw(
				_("Overtime must be approved before the authorized work begins."),
				title=_("Retroactive approval is not allowed"),
			)

		if self.overtime_work_call:
			if not self.flags.get("generated_from_overtime_work_call"):
				frappe.throw(
					_("Work-call authorizations can only be submitted by their source work call."),
					frappe.PermissionError,
				)
			work_call = frappe.get_doc("Overtime Work Call", self.overtime_work_call)
			if work_call.docstatus != 1:
				frappe.throw(_("The source overtime work call must be submitted."))
			approved_by = work_call.authorized_by or frappe.session.user
		elif not is_assigned_approver(self.approver, frappe.session.user):
			frappe.throw(
				_("Only the assigned approver {0} may submit this authorization.").format(
					frappe.bold(self.approver)
				),
				frappe.PermissionError,
			)
		else:
			approved_by = frappe.session.user

		self.status = "Approved"
		self.approved_by = approved_by
		self.approved_on = now_datetime()
		self.reconciliation_status = "Scheduled"

	def on_cancel(self):
		self.db_set("status", "Cancelled", update_modified=False)

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
		apply_employee_approver_snapshot(self, employee)
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

	def _validate_work_call_source(self):
		if not self.overtime_work_call:
			return
		if not self.flags.get("generated_from_overtime_work_call") and self.is_new():
			frappe.throw(
				_("Overtime Work Call is assigned automatically and cannot be supplied manually."),
				frappe.PermissionError,
			)
		work_call = frappe.get_doc("Overtime Work Call", self.overtime_work_call)
		if work_call.docstatus != 1:
			frappe.throw(_("The source overtime work call must be submitted."))
		if self.employee not in {row.employee for row in work_call.employees}:
			frappe.throw(_("Employee is not included in the source overtime work call."))
		matching_date = next(
			(
				row
				for row in work_call.dates
				if getdate(row.work_date) == getdate(self.work_date)
			),
			None,
		)
		if not matching_date:
			frappe.throw(_("Work Date is not included in the source overtime work call."))
		from powerpro.payroll_rules.overtime_work_call import build_authorization_window

		expected_start, expected_end = build_authorization_window(
			matching_date.work_date,
			matching_date.start_time,
			matching_date.end_time,
		)
		if (
			get_datetime(self.authorization_start) != expected_start
			or get_datetime(self.authorization_end) != expected_end
			or abs(flt(self.maximum_hours) - flt(matching_date.requested_hours)) > 0.0001
		):
			frappe.throw(
				_("Authorization window does not match the submitted overtime work call.")
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
