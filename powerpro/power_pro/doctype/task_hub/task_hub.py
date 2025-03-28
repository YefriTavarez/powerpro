# Copyright (c) 2025, Yefri Tavarez and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TaskHub(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		exp_end_date: DF.Date | None
		exp_start_date: DF.Date | None
		project: DF.Link | None
		responsible: DF.Link | None
		status: DF.Literal["", "Open", "Working", "Overdue", "Pending Review", "Completed", "Cancelled"]
	# end: auto-generated types

	@frappe.whitelist()
	def fetch_tasks(self, filters):
		out = list()
		or_filters = dict()

		exp_start_date = filters.get("exp_start_date")
		if exp_end_date:
			or_filters["exp_start_date"] = exp_start_date

		exp_end_date = filters.get("exp_end_date")
		if exp_end_date:
			or_filters["exp_end_date"] = exp_end_date

		if "exp_start_date" in filters:
			del filters["exp_start_date"]

		if "exp_end_date" in filters:
			del filters["exp_end_date"]

		for task_id in frappe.get_list(
			"Task", filters=filters, or_filters=or_filters, pluck="name"
		):
			task = get_task(task_id)

			out.append({
				"id": task.name,
				"subject": task.subject,
				"status": task.status,
				"date": task.exp_start_date,
				"due_date": task.exp_end_date,
				"project": task.project,
				"responsible": ", ".join([d.user for d in task.users]),
			})

		return out
	
	def db_insert(self, *args, **kwargs):
		frappe.throw("No se puede insertar un documento de tipo Task Hub")

	def delete(self):
		pass

	def load_from_db(self):
		pass

	def db_update(self):
		pass

	@staticmethod
	def get_list(args):
		pass

	@staticmethod
	def get_count(args):
		pass

	@staticmethod
	def get_stats(args):
		pass

	_table_fieldnames: list[str] = []


def get_task(name):
	doctype = "Task"
	return frappe.get_doc(doctype, name)
