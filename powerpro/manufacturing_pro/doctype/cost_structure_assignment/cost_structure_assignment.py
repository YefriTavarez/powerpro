# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CostStructureAssignment(Document):
	pass


def get_assigned_cost_structure(employee, on_date):
	if not employee or not on_date:
		return None
	cost_structure = frappe.db.sql(
		"""
		select cost_structure from `tabSalary Structure Assignment`
		where employee=%(employee)s
		and docstatus = 1
		and %(on_date)s >= from_date order by from_date desc limit 1""",
		{
			"employee": employee,
			"on_date": on_date,
		},
	)

	return cost_structure[0][0] if cost_structure else None
