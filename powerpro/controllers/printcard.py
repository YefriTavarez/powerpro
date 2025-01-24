# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import io
from weasyprint import HTML, CSS

import frappe


@frappe.whitelist()
def generate_pdf_for_printcard(canvas, printcard):
	cv = frappe.get_doc("PrintCard Canvas", canvas)
	pc = frappe.get_doc("PrintCard", printcard)

	html = frappe.render_template(f"""
		<div>
			{cv.codigo_html}
			<style>
				{cv.codigo_css}
				@page {{
					size: {cv.ancho_pdf}in {cv.alto_pdf}in;
					margin: 0in; /* Set margins (optional) */
				}}
			</style>
		</div>
	""", {
		"doc": pc,
	})

	# Generate the PDF and write to the buffer
	pdf_buffer = io.BytesIO()
	HTML(string=html).write_pdf(pdf_buffer)


	frappe.local.response.filename = "{name}.pdf".format(name=printcard.replace(" ", "-").replace("/", "-"))
	frappe.local.response.filecontent = pdf_buffer.getvalue()
	frappe.local.response.type = "pdf"
