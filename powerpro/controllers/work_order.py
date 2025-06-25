# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

from erpnext.manufacturing.doctype.work_order import work_order


class WorkOrder(work_order.WorkOrder):
	def autoname(self):
		self.name = self.project \
			.replace("PROY-", "OPR-")
