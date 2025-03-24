# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe
from frappe.model import no_value_fields

from erpnext.projects.doctype.project_template import project_template


class ProjectTemplate(project_template.ProjectTemplate):
	def onload(self):
		self.set_project_docfields()

	def validate(self):
		self.validate_project_docfields()
	
	def before_insert(self):
		self.set_project_docfields()

	def validate_project_docfields(self):
		for field in self.project_docfields:
			if not field.reqd:
				continue

			if field.hidden:
				frappe.throw(
					f"""El campo {field.label!r} en la fila #{field.idx} no puede ser oculto y requerido al mismo tiempo""",
					title="Error de Validación"
				)
			
			if field.read_only:
				frappe.throw(
					f"""El campo {field.label!r} en la fila #{field.idx} no puede ser de solo lectura y requerido al mismo tiempo""",
					title="Error de Validación"
				)

	@frappe.whitelist()
	def set_project_docfields(self, for_reload=False, with_memory=False):
		if with_memory:
			if not for_reload:
				frappe.throw(
					"La opción 'with_memory' solo puede ser usada en conjunto con la opción 'for_reload'",
					title="Error de Validación"
				)
			
			self.before_save_project_docfields = self.project_docfields

		if for_reload:
			self.project_docfields = []

		if not self.project_docfields:
			for df in get_project_fields():
				self.append("project_docfields", {
					"label": frappe._(df.label, "es"),
					"fieldname": df.fieldname,
				})
		
		if with_memory:
			for field in self.before_save_project_docfields:
				# will find the previous value for hidden, reqd and read_only fields
				# and set it back
				fieldname = field.fieldname
				[_field] = self.get("project_docfields", {"fieldname": fieldname})
				if _field:
					_field.hidden = field.hidden
					_field.reqd = field.reqd
					_field.read_only = field.read_only
				
		
		if for_reload:
			self.flags.ignore_mandatory = True
			self.save()

def get_project_fields():
	meta = frappe.get_meta("Project")

	doctype = frappe.get_doc("DocType", "Project")

	def _get_read_only_fields():
		return [
			field.fieldname
			for field in doctype.fields
			if field.read_only
		]
	
	def _get_hidden_fields():
		return [
			field.fieldname
			for field in doctype.fields
			if field.hidden
		]
	
	def _get_reqd_fields():
		return [
			field.fieldname
			for field in doctype.fields
			if field.reqd
		]

	# only value fields
	value_fields = [
		field
		for field in meta.fields
		if field.fieldtype not in no_value_fields
	]

	# get hidden fields
	hidden_fields = _get_hidden_fields()

	# get reqd fields
	reqd_fields = _get_reqd_fields()

	non_negotiable_fields = [
		"naming_series",
		"project_name",
		"status",
		"project_type",
		"project_template",
		"company"
	]

	# get read_only fields
	read_only_fields = _get_read_only_fields()

	# exclude reqd and read_only fields
	exclude_fields = set(
		reqd_fields + non_negotiable_fields + hidden_fields + read_only_fields
	)

	# get project fields
	return [
		field
		for field in value_fields
		if field.fieldname not in exclude_fields
	]


@frappe.whitelist()
def get_project_docfields(project_template_id=None):
	if project_template_id:
		template = get_project_template(project_template_id)

		fields = template.project_docfields
	else:
		fields = get_project_fields()

	return [
		{
			"label": field.label,
			"fieldname": field.fieldname,
			"reqd": field.reqd,
			"read_only": field.read_only,
			"hidden": field.hidden,
		} for field in fields
	]


def get_project_template(name):
	doctype= "Project Template"
	return frappe.get_doc(doctype, name)
