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
