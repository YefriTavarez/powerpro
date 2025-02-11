# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt


import frappe


def execute():
	create_property_setters()
	create_custom_fields()
	create_translation_records()


def create_property_setters():
	docs = """
		[
			{"name":"Supplier-supplier_type-hidden","owner":"Administrator","creation":"2025-02-10 21:21:00.442498","modified":"2025-02-10 21:21:00.442498","modified_by":"Administrator","docstatus":0,"idx":0,"is_system_generated":0,"doctype_or_field":"DocField","doc_type":"Supplier","field_name":"supplier_type","property":"hidden","property_type":"Check","value":"1","doctype":"Property Setter","__last_sync_on":"2025-02-11T02:44:38.319Z"},
			{"name":"Supplier-supplier_type-fetch_from","owner":"Administrator","creation":"2025-02-10 21:21:14.617366","modified":"2025-02-10 21:21:14.617366","modified_by":"Administrator","docstatus":0,"idx":0,"is_system_generated":0,"doctype_or_field":"DocField","doc_type":"Supplier","field_name":"supplier_type","property":"fetch_from","property_type":"Small Text","value":"supplier_classification.supplier_type","doctype":"Property Setter","__last_sync_on":"2025-02-11T02:45:06.043Z"}
		]
	"""

	for doc in frappe.parse_json(docs):
		if not frappe.db.exists("Property Setter", doc.get("name")):
			frappe.get_doc(doc).insert()


def create_custom_fields():
	docs = """[{"name":"Supplier-supplier_classification","owner":"Administrator","creation":"2025-02-10 21:21:00.499390","modified":"2025-02-10 21:21:00.499390","modified_by":"Administrator","docstatus":0,"idx":6,"is_system_generated":0,"dt":"Supplier","label":"Supplier Classification","fieldname":"supplier_classification","insert_after":"supplier_group","length":0,"fieldtype":"Link","precision":"","hide_seconds":0,"hide_days":0,"options":"Supplier Classification","sort_options":0,"fetch_if_empty":0,"collapsible":0,"non_negative":0,"reqd":0,"unique":0,"is_virtual":0,"read_only":0,"ignore_user_permissions":0,"hidden":0,"print_hide":0,"print_hide_if_no_value":0,"no_copy":0,"allow_on_submit":0,"in_list_view":0,"in_standard_filter":0,"in_global_search":0,"in_preview":0,"bold":0,"report_hide":0,"search_index":0,"allow_in_quick_entry":0,"ignore_xss_filter":0,"translatable":0,"hide_border":0,"show_dashboard":0,"permlevel":0,"columns":0,"doctype":"Custom Field","__last_sync_on":"2025-02-11T02:41:53.503Z"}]"""

	for doc in frappe.parse_json(docs):
		if not frappe.db.exists("Custom Field", doc.get("name")):
			frappe.get_doc(doc).insert()



def create_translation_records():
	docs = """[{"name":"130d28ud4j","owner":"Administrator","creation":"2025-02-10 21:27:53.271897","modified":"2025-02-10 21:27:53.271897","modified_by":"Administrator","docstatus":0,"idx":0,"contributed":0,"language":"es-DO","source_text":"Supplier Classification","context":null,"translated_text":"Clasificación del Proveedor","contribution_status":"","contribution_docname":null,"doctype":"Translation","__last_sync_on":"2025-02-11T01:27:53.300Z"}]"""

	for doc in frappe.parse_json(docs):
		if not frappe.db.exists("Translation", doc.get("name")):
			frappe.get_doc(doc).insert()
