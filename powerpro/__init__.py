__version__ = "1.0.1"

# from typing import TYPE_CHECKING


# hack: to load the overridden controller of a custom doctype.
if False: # why type checking? I think this is to speed up the import process
	from frappe.model import base_document

	def import_controller(doctype):
		import frappe
		from frappe.model.base_document import (
			BaseDocument,
			load_doctype_module,
			DOCTYPES_FOR_DOCTYPE,
		)

		from frappe.model.document import Document
		from frappe.utils.nestedset import NestedSet

		module_name = "Core"
		if doctype not in DOCTYPES_FOR_DOCTYPE:
			doctype_info = frappe.db.get_value("DocType", doctype, fieldname="*")
			if doctype_info:
				if doctype_info.custom:
					# check first if there is an override_doctype_class for this doctype
					# before defaulting the standard Document and NestedSet classes
					if doctype in frappe.get_hooks("override_doctype_class"):
						class_ = frappe.get_hooks("override_doctype_class")[doctype][-1]
						module_path, classname = class_.rsplit(".", 1)
						module = frappe.get_module(module_path)
						return getattr(module, classname)

					return NestedSet if doctype_info.is_tree else Document
				module_name = doctype_info.module

		module_path = None
		class_overrides = frappe.get_hooks("override_doctype_class")
		if class_overrides and class_overrides.get(doctype):
			import_path = class_overrides[doctype][-1]
			module_path, classname = import_path.rsplit(".", 1)
			module = frappe.get_module(module_path)

		else:
			module = load_doctype_module(doctype, module_name)
			classname = doctype.replace(" ", "").replace("-", "")

		class_ = getattr(module, classname, None)
		if class_ is None:
			raise ImportError(
				doctype
				if module_path is None
				else f"{doctype}: {classname} does not exist in module {module_path}"
			)

		if not issubclass(class_, BaseDocument):
			raise ImportError(f"{doctype}: {classname} is not a subclass of BaseDocument")

		return class_

	# do a monkey patch to the base_document module
	base_document.import_controller = import_controller
