# Copyright (c) 2025, Yefri Tavarez and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from jinja2 import Template


class AttachmentType(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.
	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from powerpro.power_pro.doctype.attachment_doctypes.attachment_doctypes import AttachmentDocTypes

		allow_more_than_one: DF.Check
		attachment_doctypes: DF.TableMultiSelect[AttachmentDocTypes]
		attachment_name: DF.Data | None
		max_allowed: DF.Int
		prefix: DF.Data | None
		naming_template: DF.Data | None
		sequence_padding: DF.Int
	# end: auto-generated types
	
	def next_name(self, doc=None, reference_doctype=None, reference_name=None):
		if not doc and not reference_doctype and not reference_name:
			raise ValueError("Either doc or reference_doctype and reference_name must be provided.")

		if not doc:
			doc = frappe.get_doc(reference_doctype, reference_name)
		
		if not doc:
			raise ValueError("Document not found.")



		if not self.naming_template:
			import random, string
			return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

		context = doc.as_dict() if hasattr(doc, "as_dict") else doc
		context.update({
			"frappe": frappe,
		})

		template_text = self.naming_template.rsplit(".", 1)[0]
		template = Template(template_text)
		base_prefix = template.render(context)

		last_file = frappe.db.sql(
			"""
			SELECT file_name
			FROM `tabFile`
			WHERE file_name LIKE %s
			ORDER BY CAST(SUBSTRING_INDEX(file_name, '-', -1) AS UNSIGNED) DESC
			LIMIT 1
			""",
			(f"{base_prefix}%",),
			as_dict=True
		)

		next_number = 1
		if last_file:
			try:
				last_number = int(last_file[0]["file_name"].rsplit('-', 1)[-1])
				next_number = last_number + 1
			except ValueError:
				pass

		padded_seq = f"{next_number:0{self.sequence_padding}}"
		return f"{base_prefix}{padded_seq}"