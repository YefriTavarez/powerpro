# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import base64

import frappe

from powerpro.controllers.printcard import helper as printcard_helper
from powerpro.controllers.printcard_pdf_client import PrintCardPdfClient

@frappe.whitelist()
def get_printcard_list(arte_id):
    """Fetches a list of PrintCard records matching the given arte_id (codigo_arte)."""
    if not arte_id:
        frappe.throw("Parameter 'arte_id' is required")

    results = frappe.db.get_list(
        "PrintCard",
        filters={"codigo_arte": arte_id},
        fields=["name", "estado", "version_arte_interna", "version"]
    )

    # Concatenate 'version_arte_interna' and 'version' using a dot (.)
    for record in results:
        record["version_combined"] = f"{record['version_arte_interna']}.{record['version']}"

    # sort records by 'version_combined' in descending order
    results = sorted(results, key=lambda x: x["version_combined"], reverse=True)
    
    return results


@frappe.whitelist()
def request_remote_printcard_pdf(printcard_name, canvas_name=None):
	"""Build payload from local PrintCard/Canvas and request DB-free PDF on remote server."""
	if not printcard_name:
		frappe.throw("Parameter 'printcard_name' is required.")

	printcard = printcard_helper.get_princard(printcard_name)
	canvas_doc = _resolve_canvas_for_printcard(printcard, canvas_name)
	pdf_base64 = _read_printcard_pdf_as_base64(printcard.archivo)
	lookups = _build_template_lookups(printcard)

	payload = {
		"pdf_base64": pdf_base64,
		"doc": printcard.as_dict(),
		"canvas": canvas_doc.as_dict(),
		"lookups": lookups,
		"safety": {
			"allow_frappe_proxy": False,
		},
	}

	client = PrintCardPdfClient()
	response = client.generate_pdf_response(payload)
	return {
		"ok": True,
		"pdf_base64": response.get("pdf_base64"),
		"filename": response.get("filename"),
	}


def _resolve_canvas_for_printcard(printcard, canvas_name=None):
	if canvas_name:
		return printcard_helper.get_canvas(canvas_name)

	if not printcard.archivo:
		frappe.throw(f"PrintCard '{printcard.name}' has no source file in 'archivo'.")

	pdf_path = printcard_helper.get_file_path(printcard.archivo)
	width, height = printcard_helper.pdf_manager.get_pdf_dimensions(pdf_path)
	best_canvas_name = printcard_helper.get_best_canvas(width, height, raise_if_empty=True)
	return printcard_helper.get_canvas(best_canvas_name)


def _read_printcard_pdf_as_base64(file_url):
	if not file_url:
		frappe.throw("Missing source PDF file URL.")

	file_path = printcard_helper.get_file_path(file_url)
	with open(file_path, "rb") as fp:
		return base64.b64encode(fp.read()).decode("utf-8")


def _build_template_lookups(printcard):
	lookups = {"Raw Material": {}}
	if not printcard.material:
		return lookups

	description = frappe.db.get_value("Raw Material", printcard.material, "description")
	if description is None:
		return lookups

	lookups["Raw Material"][printcard.material] = {
		"description": description,
	}
	return lookups
