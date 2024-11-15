# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

from typing import Optional

import frappe

from semver import Version

from frappe import _
from frappe.model import naming
from erpnext.quality_management.doctype.quality_procedure import quality_procedure

class QualityProcedure(quality_procedure.QualityProcedure):
	def autoname(self):
		department_prefix = self.department[:3]
		naming_series = f"PRO-CAL-{department_prefix.upper()}-.#####"
		self.name = naming.make_autoname(naming_series)

	def validate(self):
		if not self.flags.internal_save and self.is_new():
			self.revision = "1.0.0"
			return # ignore new documents

		if not self.flags.internal_save:
			frappe.throw(
				_("You can't update directly a Quality Procedure. Use the buttons instead.")
			)

	@frappe.whitelist()
	def bump_major(self, autosave: bool = False) -> Optional[str]:
		version = self.get_version()
		self._revision = str(version.bump_major())

		if autosave:
			return self.supersede()

	@frappe.whitelist()
	def bump_minor(self, autosave: bool = False) -> Optional[str]:
		version = self.get_version()
		self._revision = str(version.bump_minor())

		if autosave:
			return self.supersede()

	@frappe.whitelist()
	def bump_patch(self, autosave: bool = False) -> Optional[str]:
		version = self.get_version()
		self._revision = str(version.bump_patch())

		if autosave:
			return self.supersede()

	@frappe.whitelist()
	def save_only(self):
		self.flags.internal_save = True
		self.save()

	def supersede(self) -> None:
		self.queue_action("mark_as_superseded", enqueue_after_commit=True)

		copy = frappe.copy_doc(self)
		copy.revision = self._revision
		copy.status = self.status

		copy.closest_seed = self.name

		if not copy.seed:
			copy.seed = copy.closest_seed

		copy.flags.ignore_permissions = True
		copy.flags.internal_save = True
		copy.insert()

		return copy.name

	def mark_as_superseded(self):
		self.db_set("status", "Superseded")

	def get_version(self) -> Version:
		return Version.parse(self.revision)

	revision: str = None
	department: str = None
	created_by: str = None
	created_on: str = None
	reviewed_by: str = None
	reviewed_on: str = None
