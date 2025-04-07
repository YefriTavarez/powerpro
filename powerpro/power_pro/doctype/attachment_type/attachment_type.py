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
