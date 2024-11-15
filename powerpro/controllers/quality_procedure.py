# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

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
		if not self.flags.internal_save:
			frappe.throw(
				_("You can't update directly a Quality Procedure. Use the buttons instead.")
			)

	@frappe.whitelist()
	def bump_major(self, autosave: bool = False):
		version = self.get_version()
		self.revision = str(version.bump_major())

		if autosave:
			self.db_set("revision", self.revision)

	@frappe.whitelist()
	def bump_minor(self, autosave: bool = False):
		version = self.get_version()
		self.revision = str(version.bump_minor())

		if autosave:
			self.db_set("revision", self.revision)

	@frappe.whitelist()
	def bump_patch(self, autosave: bool = False):
		version = self.get_version()
		self.revision = str(version.bump_patch())

		if autosave:
			self.db_set("revision", self.revision)

	def save_only(self):
		self.flags.internal_save = True
		self.save()

	def get_version(self) -> Version:
		return Version.parse(self.revision)

	revision: str = None
	department: str = None
	created_by: str = None
	created_on: str = None
	reviewed_by: str = None
	reviewed_on: str = None
