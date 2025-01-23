# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt


import frappe
from frappe.utils.pdf import get_pdf

@frappe.whitelist()
def generate_pdf_for_printcard(canvas, printcard):
	cv = frappe.get_doc("PrintCard Canvas", canvas)
	pc = frappe.get_doc("PrintCard", printcard)

	html = frappe.render_template(f"""
		<div>
			{cv.codigo_html}
			<style>
				{cv.codigo_css}
			</style>
		</div>
	""", {
		"doc": pc,
	})

	pdf_options = {
		"page-width": f"{cv.ancho_pdf}in",
		"page-height": f"{cv.alto_pdf}in",
		"margin-top": "0",
		"margin-right": "0",
		"margin-bottom": "0",
		"margin-left": "0",
		"no-outline": None,
		# "disable-smart-shrinking": None,
		# "print-media-type": None,
		# "background": None
	}


	output = None # for now

	pdf_file = get_pdf(html, options=pdf_options, output=output)

	frappe.local.response.filename = "{name}.pdf".format(name=printcard.replace(" ", "-").replace("/", "-"))
	frappe.local.response.filecontent = pdf_file
	frappe.local.response.type = "pdf"
