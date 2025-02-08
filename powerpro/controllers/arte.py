# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import shutil

import frappe
from frappe.model.document import Document


class Arte(Document):
	def on_update(self):
		self.rename_archivo_actual()
	
	def rename_archivo_actual(self):
		if not self.archivo_actual:
			return

		filename = f"[AP]{self.codigo_arte}.v{self.version_actual}.pdf"

		if filename in self.archivo_actual:
			return # the current file is already named correctly
		
		# let's rename the file in the file system
		filepath = self.rename_file(self.archivo_actual, filename)

		self.update_file_refs(self.archivo_actual, filepath)

		# let's update the row in the database
		self.archivo_actual = filepath

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
		# shutil.move(
		# 	f"{base_path}{old_filepath}",
		# 	f"{base_path}/public/files/{new_filename}",
		# )

		# copy instead
		shutil.copy(
			f"{base_path}{old_filepath}",
			f"{base_path}/public/files/{new_filename}",
		)

		return f"/files/{new_filename}"
	
	def update_file_refs(self, old_filepath, new_filepath):
		for (
			name,
			attached_to_doctype,
			attached_to_name,
			attached_to_field,
		) in frappe.db.sql(f"""
			Select
				name,
				attached_to_doctype,
				attached_to_name,
				attached_to_field
			From
				`tabFile`
			Where
				file_url = {old_filepath!r}
		"""):
			if attached_to_doctype \
				and attached_to_name \
				and attached_to_field:
				frappe.db.set_value(
					attached_to_doctype,
					attached_to_name,
					attached_to_field,
					new_filepath,
				)

			frappe.db.set_value(
				"File",
				name,
				"file_url",
				new_filepath,
			)

	def silently_self_update(self):
		self.db_update()
		self.notify_update()

		frappe.msgprint(
			f"El archivo actual ha sido renombrado a {self.archivo_actual}",
			indicator="green",
			alert=True,
		)
