# Copyright (c) 2025, Yefri Tavarez and contributors
# For license information, please see license.txt

from typing import Union, List, TYPE_CHECKING

if TYPE_CHECKING:
	import datetime

import frappe
from frappe.model.document import Document


from . import actions_controller

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
		task_id: DF.Link | None
	# end: auto-generated types

	@frappe.whitelist()
	def fetch_tasks(self, filters):
		out = list()
		or_filters = dict()

		status = filters.get("status")

		if not status:
			filters["status"] = ["not in", ["Cancelled", "Completed", "Template"]]

		user = filters.get("responsible")
		if "responsible" in filters:
			del filters["responsible"]

		exp_start_date = filters.get("exp_start_date")
		if exp_start_date:
			or_filters["exp_start_date"] = exp_start_date

		exp_end_date = filters.get("exp_end_date")
		if exp_end_date:
			or_filters["exp_end_date"] = exp_end_date
			or_filters["exp_end_date"] = exp_end_date

		if "exp_start_date" in filters:
			del filters["exp_start_date"]

		if "exp_end_date" in filters:
			del filters["exp_end_date"]

		filtrs = convert_filters_dict_to_list(filters, "Task")
		filtrs.append([
			["Task Responsible", "user", "=", user],
		])

		# or_filters=or_filters,
		for task_id in frappe.get_list(
			"Task", filters=filters, or_filters=or_filters, pluck="name"
		):
			task = get_task(task_id)

			out.append({
				"id": task.name,
				"title": task.subject,
				"status": task.status.lower(),
				"date": task.exp_start_date,
				"due_date": task.exp_end_date,
				"project": task.project,
				"user": ", ".join([d.user for d in task.users if d.user]),
			})

		return out

	@frappe.whitelist()	
	def reopen_task(self, task_id):
		return actions_controller.reopen_task(self, task_id)

	@frappe.whitelist()
	def complete_task(self, task_id):
		return actions_controller.complete_task(self, task_id)

	@frappe.whitelist()
	def change_status(self, task_id, status):
		return actions_controller.change_status(self, task_id, status)

	@frappe.whitelist()
	def request_revision(self, task_id):
		return actions_controller.request_revision(self, task_id)

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
	modified: Union[str, "datetime.datetime"] | None = None


def get_task(name):
	doctype = "Task"
	return frappe.get_doc(doctype, name)


def convert_filters_dict_to_list(filters: dict, doctype: str) -> List[list]:
	out = list()

	for key, value in filters.items():
		out.append([doctype, key, "=", value])

	return out
