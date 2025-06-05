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

		user = filters.get("responsible")
		if "responsible" in filters:
			del filters["responsible"]

		exp_start_date = filters.get("exp_start_date")
		if exp_start_date:
			or_filters["exp_start_date"] = exp_start_date

		exp_end_date = filters.get("exp_end_date")
		if exp_end_date:
			or_filters["exp_end_date"] = exp_end_date

		if "exp_start_date" in filters:
			del filters["exp_start_date"]

		if "exp_end_date" in filters:
			del filters["exp_end_date"]

		filtrs = convert_filters_dict_to_list(filters, "Task")

		if not filters.get("status"):
			filtrs.append(["Task", "status", "not in", ["Cancelled", "Completed", "Template"]])

		# ensure none authorized users can see other users tasks
		if not has_role(
			get_project_manager()
		):
			user = frappe.session.user

		if user:
			filtrs.append(["Task Responsible", "user", "=", user])

		task_ids = frappe.get_list(
			"Task", filters=filtrs, or_filters=or_filters, pluck="name", order_by="name asc",
		)

		# Filter out tasks that are blocked by other tasks
		unblocked_task_ids = []
		for task_id_item in task_ids:
			blocking_tasks = get_blocking_tasks(task_id_item)
			if not blocking_tasks:
				unblocked_task_ids.append(task_id_item)
				continue

			is_blocked = False
			for blocking_task_name in blocking_tasks:
				blocking_task_doc = get_task(blocking_task_name)
				if blocking_task_doc.status not in ["Completed", "Cancelled"]:
					is_blocked = True
					break
			if not is_blocked:
				unblocked_task_ids.append(task_id_item)

		# or_filters=or_filters,
		for task_id in unblocked_task_ids:
			task = get_task(task_id)

			out.append({
				"id": task.name,
				"title": task.subject,
				"status": task.status.lower().replace(" ", "-"),
				"date": task.exp_start_date,
				"due_date": task.exp_end_date,
				"project": task.project,
				"priority": task.priority,
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


def get_blocking_tasks(task_name: str) -> List[str]:
	"""Get tasks that are blocking the given task."""
	blocking_tasks = frappe.get_all(
		"Task Depends On",
		filters={"parent": task_name, "parenttype": "Task"},
		pluck="task",
	)
	return blocking_tasks


# Define a type alias for the Task document for better type hinting
if TYPE_CHECKING:
	class Task(Document):
		name: str
		subject: str
		status: str
		exp_start_date: Union[str, "datetime.date"] | None
		exp_end_date: Union[str, "datetime.date"] | None
		project: str | None
		priority: str | None
		users: List[Document] # Assuming users is a list of child documents with a 'user' field


def get_task(name) -> "Task": # type: ignore
	doctype = "Task"
	return frappe.get_doc(doctype, name)


def convert_filters_dict_to_list(filters: dict, doctype: str) -> List[list]:
	out = list()

	for fieldname, value in filters.items():
		out.append([ doctype, fieldname, "=", value ])

	return out


def get_project_manager() -> str:
	"""Get the project manager from the settings."""
	settings = frappe.get_single("Projects Settings")

	return settings.project_manager or "System Manager"


def has_role(role: str) -> bool:
	"""Check if the user has a specific role."""
	return role in frappe.get_roles()
