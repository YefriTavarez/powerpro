# Copyright (c) 2026, PowerPro contributors

import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	_validate_filters(filters)
	data = _get_data(filters)
	return get_columns(), data, None, None, get_report_summary(data)


def get_columns():
	return [
		{"fieldname": "overtime_work_call", "label": _("Convocatoria"), "fieldtype": "Link", "options": "Overtime Work Call", "width": 150},
		{"fieldname": "employee_name", "label": _("Employee Name"), "fieldtype": "Data", "width": 210},
		{"fieldname": "department", "label": _("Department"), "fieldtype": "Link", "options": "Department", "width": 150},
		{"fieldname": "work_date", "label": _("Work Date"), "fieldtype": "Date", "width": 105},
		{"fieldname": "authorization_start", "label": _("Requested Start"), "fieldtype": "Datetime", "width": 155},
		{"fieldname": "authorization_end", "label": _("Requested End"), "fieldtype": "Datetime", "width": 155},
		{"fieldname": "maximum_hours", "label": _("Requested Hours"), "fieldtype": "Float", "precision": 2, "width": 105},
		{"fieldname": "actual_start", "label": _("Actual Start"), "fieldtype": "Datetime", "width": 155},
		{"fieldname": "actual_end", "label": _("Actual End"), "fieldtype": "Datetime", "width": 155},
		{"fieldname": "verified_hours", "label": _("Verified Hours"), "fieldtype": "Float", "precision": 2, "width": 105},
		{"fieldname": "missing_hours", "label": _("Missing Hours"), "fieldtype": "Float", "precision": 2, "width": 100},
		{"fieldname": "unapproved_hours", "label": _("Unapproved Hours"), "fieldtype": "Float", "precision": 2, "width": 115},
		{"fieldname": "adherence_percent", "label": _("Adherence"), "fieldtype": "Percent", "precision": 2, "width": 95},
		{"fieldname": "reconciliation_status", "label": _("Status"), "fieldtype": "Data", "width": 120},
		{"fieldname": "day_classification", "label": _("Day Classification"), "fieldtype": "Data", "width": 150},
		{"fieldname": "name", "label": _("Authorization"), "fieldtype": "Link", "options": "Overtime Authorization", "width": 150},
	]


def _validate_filters(filters):
	if not all(filters.get(field) for field in ("company", "from_date", "to_date")):
		frappe.throw(_("Company, From Date, and To Date are required."))
	if getdate(filters.from_date) > getdate(filters.to_date):
		frappe.throw(_("From Date cannot be after To Date."))


def _get_data(filters):
	conditions = {
		"company": filters.company,
		"work_date": ["between", [filters.from_date, filters.to_date]],
		"docstatus": 1,
		"overtime_work_call": ["is", "set"],
	}
	for fieldname in ("employee", "department", "reconciliation_status"):
		if filters.get(fieldname):
			conditions[fieldname] = filters[fieldname]
	return frappe.get_list(
		"Overtime Authorization",
		filters=conditions,
		fields=[
			"name",
			"overtime_work_call",
			"employee",
			"employee_name",
			"department",
			"work_date",
			"authorization_start",
			"authorization_end",
			"maximum_hours",
			"actual_start",
			"actual_end",
			"verified_hours",
			"missing_hours",
			"unapproved_hours",
			"adherence_percent",
			"reconciliation_status",
			"day_classification",
		],
		order_by="work_date asc, employee_name asc, name asc",
		limit_page_length=0,
	)


def get_report_summary(data):
	requested = sum(flt(row.maximum_hours) for row in data)
	verified = sum(flt(row.verified_hours) for row in data)
	adherence = min((verified / requested * 100) if requested else 0, 100)
	return [
		{"value": len({row.employee for row in data}), "label": _("Employees"), "datatype": "Int", "indicator": "blue"},
		{"value": round(requested, 2), "label": _("Requested Hours"), "datatype": "Float", "indicator": "blue"},
		{"value": round(verified, 2), "label": _("Verified Hours"), "datatype": "Float", "indicator": "green"},
		{"value": round(adherence, 2), "label": _("Adherence"), "datatype": "Percent", "indicator": "green" if adherence >= 99.99 else "orange"},
	]
