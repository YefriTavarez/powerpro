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
		"get_contrast": get_contrast,
		"frappe": frappe._dict({
			"get_value": frappe.db.get_value,
		})
	})

	# Generate the PDF and write to the buffer
	pdf_buffer = io.BytesIO()
	HTML(string=html).write_pdf(pdf_buffer)


	frappe.local.response.filename = "{name}.pdf".format(name=printcard.replace(" ", "-").replace("/", "-"))
	frappe.local.response.filecontent = pdf_buffer.getvalue()
	frappe.local.response.type = "pdf"


def get_contrast(hex_color):
    """
    Determines the most legible text color (black or white) based on the background color.
    Uses the WCAG luminance formula.
    
    Args:
        hex_color (str): Background color in hexadecimal format (e.g., "#141c37").
    
    Returns:
        str: The best contrast color ("#000000" for black or "#ffffff" for white).
    """
    # Convert hex color to RGB
    hex_color = hex_color.lstrip('#')  # Remove the "#" if present
    r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    
    # Calculate relative luminance (WCAG formula)
    def relative_luminance(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    luminance = 0.2126 * relative_luminance(r) + 0.7152 * relative_luminance(g) + 0.0722 * relative_luminance(b)
    
    # Return black (#000000) for light backgrounds and white (#ffffff) for dark backgrounds
    return '#000000' if luminance > 0.5 else '#ffffff'
