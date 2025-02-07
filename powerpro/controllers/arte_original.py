# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import shutil

import frappe
from frappe.model.document import Document


class ArteOriginal(Document):
	def on_update(self):
		self.rename_files_in_versiones_arte()
	
	def rename_files_in_versiones_arte(self):
		updates_count = 0
		for row in getattr(self, "versiones_arte", []):
			if not row.arte:
				continue # no file to rename

			filename = f"[AO]{self.codigo_arte}.v{row.idx}.pdf"

			if filename in row.arte:
				continue # the current file is already named correctly

			# let's rename the file in the file system
			filepath = self.rename_file(row.arte, filename)

			self.update_file_refs(row.arte, filepath)

			# let's update the row in the database
			row.arte = filepath

			updates_count += 1

		if updates_count:
			self.silently_self_update()
	
	def rename_file(self, old_filepath, new_filename):
		# old_filepath is a path /private/files/abc.pdf
		# new_filename is a filename cde.pdf
		# we need to keep the same path, but change the filename
		# /private/files/cde.pdf

		# get the base path
		base_path = frappe.utils.get_site_path()

		if old_filepath.startswith("/files"):
			old_filepath = f"/public{old_filepath}"

		# check if the file is private
		path, old_filename = old_filepath.rsplit("/", 1)

		# do the renaming
		shutil.move(
			f"{base_path}{old_filepath}",
			f"{base_path}/public/files/{new_filename}",
		)

		return f"/files/{new_filename}"

	def update_file_refs(self, old_filepath, new_filepath):
		# We need to update the file references in the database
		doctype = "File"
		fieldname = "file_url"

		frappe.db.sql(
			f"""
			UPDATE
				`tab{doctype}`
			SET
				`{fieldname}` = "{new_filepath}",
				attached_to_doctype = "Arte Original",
				attached_to_name = "{self.name}"
			WHERE
				`{fieldname}` = "{old_filepath}"
				And IfNull(`attached_to_doctype`, "") = ""
				And IfNull(`attached_to_name`, "") = ""
			"""
		)

	def silently_self_update(self):
		for child in self.get_all_children():
			child.db_update()
		
		self.db_update()
		self.notify_update()

		frappe.msgprint(
			f"Arte Original {self.name} actualizado correctamente",
			alert=True,
		)
