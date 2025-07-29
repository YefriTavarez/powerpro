# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe
from frappe import client


@frappe.whitelist()
def validate_link(doctype: str, docname: str, fields=None):
	if not isinstance(doctype, str):
		frappe.throw(_("DocType must be a string"))

	if not isinstance(docname, str):
		frappe.throw(_("Document Name must be a string"))

	if doctype != "DocType":
		parent_doctype = None
		if frappe.get_meta(doctype).istable:  # needed for links to child rows
			parent_doctype = frappe.db.get_value(doctype, docname, "parenttype")
		if not (
			frappe.has_permission(doctype, "select", parent_doctype=parent_doctype)
			or frappe.has_permission(doctype, "read", parent_doctype=parent_doctype)
		):
			frappe.throw(
				_("You do not have Read or Select Permissions for {}").format(frappe.bold(doctype)),
				frappe.PermissionError,
			)

	values = frappe._dict()

	if client.is_virtual_doctype(doctype):
		try:
			frappe.get_doc(doctype, docname)
			values.name = docname
		except frappe.DoesNotExistError:
			frappe.clear_last_message()
			frappe.msgprint(
				_("Document {0} {1} does not exist").format(frappe.bold(doctype), frappe.bold(docname)),
			)
		return values

	values.name = frappe.db.get_value(doctype, docname, cache=True)

	fields = frappe.parse_json(fields)
	if not values.name or not fields:
		return values

	try:
		# values.update(get_value(doctype, fields, docname))
		values.update( client.get_value(doctype, fields, {"name": str(docname)} ) )
	except frappe.PermissionError:
		frappe.clear_last_message()
		frappe.msgprint(
			_("You need {0} permission to fetch values from {1} {2}").format(
				frappe.bold(_("Read")), frappe.bold(doctype), frappe.bold(docname)
			),
			title=_("Cannot Fetch Values"),
			indicator="orange",
		)

	return values
