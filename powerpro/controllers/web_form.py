# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.utils import dict_with_keys
from frappe.website.utils import get_boot_data, get_sidebar_items

from frappe.website.doctype.web_form import web_form

class WebForm(web_form.WebForm):
	def get_context(self, context):
		"""Build context to render the `web_form.html` template"""
		context.in_edit_mode = False
		context.in_view_mode = False

		if frappe.form_dict.is_list:
			context.template = "website/doctype/web_form/templates/web_list.html"
		else:
			context.template = "website/doctype/web_form/templates/web_form.html"

		# check permissions
		if frappe.form_dict.name:
			if frappe.session.user == "Guest":
				frappe.throw(
					_("You need to be logged in to access this {0}.").format(self.doc_type),
					frappe.PermissionError,
				)

			if not frappe.db.exists(self.doc_type, frappe.form_dict.name):
				raise frappe.PageDoesNotExistError()

			if not self.has_web_form_permission(self.doc_type, frappe.form_dict.name):
				frappe.throw(
					_("You don't have the permissions to access this document"), frappe.PermissionError
				)

		if frappe.local.path == self.route:
			path = f"/{self.route}/list" if self.show_list else f"/{self.route}/new"
			frappe.redirect(path)

		if frappe.form_dict.is_list and not self.show_list:
			frappe.redirect(f"/{self.route}/new")

		if frappe.form_dict.is_edit and not self.allow_edit:
			context.in_view_mode = True
			frappe.redirect(f"/{self.route}/{frappe.form_dict.name}")

		if frappe.form_dict.is_edit:
			context.in_edit_mode = True

		if frappe.form_dict.is_read:
			context.in_view_mode = True

		if (
			not frappe.form_dict.is_edit
			and not frappe.form_dict.is_read
			and self.allow_edit
			and frappe.form_dict.name
		):
			context.in_edit_mode = True
			frappe.redirect(f"/{frappe.local.path}/edit")

		if (
			frappe.session.user != "Guest"
			and self.login_required
			and not self.allow_multiple
			and not frappe.form_dict.name
			and not frappe.form_dict.is_list
		):
			condition_json = json.loads(self.condition_json) if self.condition_json else []
			condition_json.append(["owner", "=", frappe.session.user])
			names = frappe.get_all(self.doc_type, filters=condition_json, pluck="name")
			if names:
				context.in_view_mode = True
				frappe.redirect(f"/{self.route}/{names[0]}")

		# Show new form when
		# - User is Guest
		# - Login not required
		route_to_new = frappe.session.user == "Guest" or not self.login_required
		if not frappe.form_dict.is_new and route_to_new:
			frappe.redirect(f"/{self.route}/new")

		self.reset_field_parent()

		# add keys from form_dict to context
		context.update(dict_with_keys(frappe.form_dict, ["is_list", "is_new", "is_edit", "is_read"]))

		for df in self.web_form_fields:
			if df.fieldtype == "Column Break":
				context.has_column_break = True
				break

		# load web form doc
		context.web_form_doc = self.as_dict(no_nulls=True)
		context.web_form_doc.update(
			dict_with_keys(context, ["is_list", "is_new", "in_edit_mode", "in_view_mode"])
		)

		if self.show_sidebar:
			context.sidebar_items = get_sidebar_items(self.website_sidebar)

		if frappe.form_dict.is_list:
			self.load_list_data(context)
		else:
			self.load_form_data(context)

		self.add_custom_context_and_script(context)
		self.load_translations(context)
		self.add_metatags(context)

		context.boot = get_boot_data()
		context.boot["link_title_doctypes"] = frappe.boot.get_link_title_doctypes()

		context.webform_banner_image = self.banner_image
		context.pop("banner_image", None)
