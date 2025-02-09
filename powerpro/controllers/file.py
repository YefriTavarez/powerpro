# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import os

import frappe
from frappe import _
from frappe.utils import get_files_path
from frappe.core.doctype.file import file


class File(file.File):
	# override the validate_file_path method
	def validate_file_path(self):
		# this is the only change in this method
		if self.is_new(): # skip for new files
			return
	
		if self.is_remote_file:
			return

		base_path = os.path.realpath(get_files_path(is_private=self.is_private))
		if not os.path.realpath(super.get_full_path()).startswith(base_path):
			frappe.throw(
				_(f"The File URL you've entered {os.path.realpath(self.get_full_path())!r} is incorrect"),
				title=_("Invalid File URL"),
			)
