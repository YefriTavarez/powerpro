# Copyright (c) 2026, PowerPro contributors
# For license information, please see license.txt

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate, now_datetime

from powerpro.controllers.overtime import reconcile_overtime_document
from powerpro.payroll_rules.overtime_work_call import (
	build_authorization_window,
	derive_reconciliation_snapshot,
	requested_hours,
	validate_requested_date_range,
)


MAX_GENERATED_AUTHORIZATIONS = 1000
MAX_REQUESTED_DATES = 366
REVIEW_STATUSES = {"Partial", "Absent", "Overrun", "Check-in Issue"}


class OvertimeWorkCall(Document):
	def before_insert(self):
		self.requested_by = frappe.session.user

	def validate(self):
		self._validate_feature_flag()
		self.requested_by = self.owner or frappe.session.user
		self._validate_employees()
		self._validate_dates()
		self._set_totals()
		if self.docstatus == 0:
			self.status = "Draft"

	def before_submit(self):
		self.check_permission("submit")
		now = now_datetime()
		for row in self.dates:
			start, _end = build_authorization_window(
				row.work_date, row.start_time, row.end_time
			)
			if start <= now:
				frappe.throw(
					_("Every overtime work call must be submitted before its first requested window begins."),
					title=_("Retroactive work calls are not allowed"),
				)
		self.status = "Authorized"
		self.authorized_by = frappe.session.user
		self.authorized_on = now

	def on_submit(self):
		self._create_authorizations()

	def on_cancel(self):
		for name in frappe.get_all(
			"Overtime Authorization",
			filters={"overtime_work_call": self.name, "docstatus": 1},
			pluck="name",
		):
			authorization = frappe.get_doc("Overtime Authorization", name)
			authorization.flags.ignore_permissions = True
			authorization.cancel()
		self.db_set("status", "Cancelled", update_modified=False)

	def _validate_feature_flag(self):
		if not frappe.db.get_single_value(
			"DGII Payroll Settings", "enable_overtime_authorization"
		):
			frappe.throw(
				_("Overtime Authorization is disabled in DGII Payroll Settings."),
				title=_("Feature disabled"),
			)

	def _validate_employees(self):
		if not self.employees:
			frappe.throw(_("Add at least one employee to the overtime work call."))
		seen = set()
		for row in self.employees:
			if not row.employee:
				frappe.throw(_("Every employee row must select an Employee."))
			if row.employee in seen:
				frappe.throw(
					_("Employee {0} appears more than once.").format(
						frappe.bold(row.employee)
					)
				)
			seen.add(row.employee)
			employee = frappe.db.get_value(
				"Employee",
				row.employee,
				[
					"employee_name",
					"company",
					"department",
					"designation",
					"default_shift",
					"status",
					"overtime_eligible",
					"overtime_approver",
				],
				as_dict=True,
			)
			if not employee or employee.status != "Active":
				frappe.throw(_("Only active employees may be included."))
			if employee.company != self.company:
				frappe.throw(
					_("Employee {0} belongs to a different company.").format(
						frappe.bold(row.employee)
					)
				)
			if not employee.overtime_eligible:
				frappe.throw(
					_("Employee {0} is not marked as overtime-eligible.").format(
						frappe.bold(employee.employee_name)
					)
				)
			if not employee.overtime_approver:
				frappe.throw(
					_("Employee {0} has no Overtime Approver configured.").format(
						frappe.bold(employee.employee_name)
					)
				)
			row.employee_name = employee.employee_name
			row.department = employee.department
			row.designation = employee.designation
			row.default_shift = employee.default_shift

	def _validate_dates(self):
		if not self.dates:
			frappe.throw(_("Generate or add at least one requested date."))
		if len(self.dates) > MAX_REQUESTED_DATES:
			frappe.throw(
				_("One overtime work call is limited to {0} requested dates.").format(
					MAX_REQUESTED_DATES
				)
			)
		seen = set()
		for row in self.dates:
			if not row.work_date:
				frappe.throw(_("Every requested date row requires a Work Date."))
			if row.work_date in seen:
				frappe.throw(
					_("Work Date {0} appears more than once.").format(
						frappe.bold(row.work_date)
					)
				)
			seen.add(row.work_date)
			row.start_time = row.start_time or self.default_start_time
			row.end_time = row.end_time or self.default_end_time
			try:
				row.requested_hours = requested_hours(
					row.work_date, row.start_time, row.end_time
				)
			except ValueError as exc:
				frappe.throw(str(exc))
			if flt(row.requested_hours) <= 0:
				frappe.throw(_("Requested hours must be greater than zero."))
		try:
			validate_requested_date_range(
				self.from_date,
				self.to_date,
				[row.work_date for row in self.dates],
			)
		except ValueError as exc:
			frappe.throw(_(str(exc)))

	def _set_totals(self):
		self.employee_count = len(self.employees)
		self.date_count = len(self.dates)
		self.authorization_count = self.employee_count * self.date_count
		if self.authorization_count > MAX_GENERATED_AUTHORIZATIONS:
			frappe.throw(
				_("One work call is limited to {0} employee/date authorizations.").format(
					MAX_GENERATED_AUTHORIZATIONS
				)
			)
		self.requested_employee_hours = round(
			sum(flt(row.requested_hours) for row in self.dates)
			* self.employee_count,
			4,
		)

	def _create_authorizations(self):
		created = 0
		for employee in self.employees:
			for requested_date in self.dates:
				start, end = build_authorization_window(
					requested_date.work_date,
					requested_date.start_time,
					requested_date.end_time,
				)
				authorization = frappe.new_doc("Overtime Authorization")
				authorization.update({
					"employee": employee.employee,
					"work_date": requested_date.work_date,
					"authorization_start": start,
					"authorization_end": end,
					"maximum_hours": requested_date.requested_hours,
					"reason": self.reason,
					"planned_settlement": self.planned_settlement,
					"overtime_work_call": self.name,
				})
				authorization.flags.generated_from_overtime_work_call = True
				authorization.insert(ignore_permissions=True)
				authorization.flags.ignore_permissions = True
				authorization.submit()
				created += 1
		if created != cint(self.authorization_count):
			frappe.throw(_("Not all expected overtime authorizations were created."))


@frappe.whitelist()
def reconcile_overtime_work_call(work_call, dry_run=1):
	"""Preview first, then optionally persist attendance and adherence snapshots."""
	doc = frappe.get_doc("Overtime Work Call", work_call)
	if not frappe.has_permission("Overtime Work Call", "read", doc=doc):
		frappe.throw(_("Not permitted to read this overtime work call."), frappe.PermissionError)
	if doc.docstatus != 1:
		frappe.throw(_("Only a submitted overtime work call can be reconciled."))
	dry_run = bool(cint(dry_run))
	if not dry_run:
		doc.check_permission("write")

	rows = []
	for name in frappe.get_all(
		"Overtime Authorization",
		filters={"overtime_work_call": doc.name, "docstatus": 1},
		pluck="name",
		order_by="work_date asc, employee_name asc",
	):
		authorization = frappe.get_doc("Overtime Authorization", name)
		if not dry_run and authorization.get("settlement_status") in {
			"Created",
			"Paid",
			"Credited",
		}:
			frappe.throw(
				_(
					"Authorization {0} is already settled; its saved reconciliation cannot be replaced."
				).format(frappe.bold(authorization.name)),
				title=_("Settlement snapshot is immutable"),
			)
		result = reconcile_overtime_document(authorization, include_weekly_context=True)
		result["source_checkins"] = result.get("source_checkins") or []
		snapshot = derive_reconciliation_snapshot(
			authorization_start=authorization.authorization_start,
			authorization_end=authorization.authorization_end,
			maximum_hours=authorization.maximum_hours,
			reconciliation=result,
			evaluation_time=now_datetime(),
		)
		row = {
			"authorization": authorization.name,
			"employee": authorization.employee,
			"employee_name": authorization.employee_name,
			"work_date": str(getdate(authorization.work_date)),
			"requested_hours": flt(authorization.maximum_hours),
			**snapshot,
			"warnings": result.get("warnings") or [],
		}
		rows.append(row)
		if not dry_run and snapshot["reconciliation_status"] != "Scheduled":
				authorization.db_set({
				**snapshot,
				"reconciliation_warnings": "\n".join(result.get("warnings") or []),
				"reconciliation_intervals": json.dumps(result.get("intervals") or [], indent=2),
				"unapproved_intervals": json.dumps(result.get("unapproved_intervals") or [], indent=2),
				"source_checkins": json.dumps(result.get("source_checkins") or [], indent=2),
				"reconciled_by": frappe.session.user,
					"reconciled_on": now_datetime(),
				})

	if len(rows) != cint(doc.authorization_count):
		frappe.throw(
			_("Expected {0} individual authorizations but found {1}.").format(
				frappe.bold(doc.authorization_count), frappe.bold(len(rows))
			),
			title=_("Authorization set is incomplete"),
		)
	summary = _summarize(rows)
	if not dry_run:
		doc.db_set({
			"status": summary["work_call_status"],
			"verified_hours": summary["verified_hours"],
			"adherence_percent": summary["adherence_percent"],
			"last_reconciled_by": frappe.session.user,
			"last_reconciled_on": now_datetime(),
		})
		doc.add_comment(
			"Info",
			_(
				"Attendance snapshot refreshed: {0} authorizations, {1} verified hours, {2}% adherence, status {3}."
			).format(
				summary["authorization_count"],
				summary["verified_hours"],
				summary["adherence_percent"],
				_(summary["work_call_status"]),
			),
		)
	return {"dry_run": dry_run, "work_call": doc.name, "rows": rows, **summary}


def _summarize(rows):
	requested = sum(flt(row.get("requested_hours")) for row in rows)
	verified = sum(flt(row.get("verified_hours")) for row in rows)
	statuses = {row.get("reconciliation_status") for row in rows}
	if statuses and statuses == {"Scheduled"}:
		work_call_status = "Authorized"
	elif "Scheduled" in statuses:
		work_call_status = "In Progress"
	elif statuses.intersection(REVIEW_STATUSES):
		work_call_status = "Needs Review"
	else:
		work_call_status = "Completed"
	return {
		"authorization_count": len(rows),
		"requested_hours": round(requested, 4),
		"verified_hours": round(verified, 4),
		"adherence_percent": round(min((verified / requested * 100) if requested else 0, 100), 2),
		"work_call_status": work_call_status,
	}
