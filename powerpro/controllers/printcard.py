# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import io
from weasyprint import HTML

import frappe

from powerpro.controllers.pdf_manager import pdf_manipulator as pdf_manager 


@frappe.whitelist()
def generate_pdf_for_printcard(canvas=None, printcard=None):
	if not printcard:
		frappe.throw("You must specify a PrintCard to generate the PDF")

	pc = frappe.get_doc("PrintCard", printcard)

	if not canvas:
		filepath = get_file_path(pc.archivo)

		width, height = pdf_manager.get_pdf_dimensions(filepath)

		canvas_list = get_canvas_list_without_ancho_specs()

		minimum_canvas_margin = get_minimum_canvas_margin()

		canvas = pdf_manager.select_best_canvas(
			width, height, canvas_list, minimum_canvas_margin
		)

	if not canvas:
		frappe.throw("No canvas found for the specified PrintCard")


	cv = frappe.get_doc("PrintCard Canvas", canvas)

	html = frappe.render_template(f"""
		<div>
			{cv.codigo_html}
			<style>
				{cv.codigo_css}
				@page {{
					size: {cv.ancho_pdf}in {cv.alto_pdf}in;
					margin: {cv.margin_top}in {cv.margin_right}in {cv.margin_bottom}in {cv.margin_left}in;
				}}
			</style>
		</div>
	""", {
		"doc": pc,
		"canvas": cv,
		"get_ink_color": get_ink_color,
		"get_constrast_of_ink_color": get_constrast_of_ink_color,
		"frappe": frappe._dict({
			"get_value": frappe.db.get_value,
		})
	})

	# Generate the PDF and write to the buffer
	pdf_buffer = io.BytesIO()
	HTML(string=html).write_pdf(pdf_buffer)
	pdf_buffer.seek(0)  # Ensure the buffer is at the beginning


	pdf_to_render = get_file_path(pc.archivo)
	
	# Render the PDF on the template
	output = pdf_manager.render_pdf_on_template(pdf_buffer, pdf_to_render, canvas=cv)


	frappe.local.response.filename = "{name}.pdf".format(name=printcard.replace(" ", "-").replace("/", "-"))
	# frappe.local.response.filecontent = pdf_buffer.getvalue()
	frappe.local.response.filecontent = output.getvalue()
	frappe.local.response.type = "pdf"


def get_file_path(filename):
	is_private=filename.startswith("/private")
	files_folder = frappe.utils.get_files_path(is_private=is_private)

	if is_private:
		filepath = filename.replace("/private/files/", "")
	else:
		filepath = filename.replace("/files/", "")

	return f"{files_folder}/{filepath}"


def get_ink_color(ink_color_id):
	doctype = "Ink Color"
	name = ink_color_id
	fieldname = "hexadecimal_color"

	return frappe.db.get_value(doctype, name, fieldname) or "#ffffff"


def get_constrast_of_ink_color(ink_color_id):
	ink_color = get_ink_color(ink_color_id)

	return get_contrast(ink_color)


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


def get_canvas_list_without_ancho_specs():
	# read all PrintCard Canvas documents
	# and return a list of tuples with the canvas dimensions
	# we need to substract the ancho_specs to the width if the canvas is horizontal
	# (orientation == "Landscape") and the alto_specs to the height if the canvas is vertical (orientation == "Portrait")

	out = list()

	for canvas in frappe.get_all("PrintCard Canvas", filters={
		"disabled": 0,
	}, fields=[
		"ancho_pdf",
		"alto_pdf",
		"ancho_specs",
		"orientation",
	]):
		if canvas.orientation == "Portrait":
			width = canvas.ancho_pdf
			height = canvas.alto_pdf - canvas.ancho_specs
		else:
			height = canvas.alto_pdf
			width = canvas.ancho_pdf - canvas.ancho_specs

		out.append((width, height))

	return out


def get_minimum_canvas_margin():
	doctype = "PreProIGC Settings"
	fieldname = "minimum_canvas_margin"

	return frappe.db.get_single_value(doctype, fieldname)
