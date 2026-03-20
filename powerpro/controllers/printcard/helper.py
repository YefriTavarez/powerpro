# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt


from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from frappe.model import document as document


import base64
import binascii
import io
import re
import uuid

from weasyprint import HTML

import frappe
from frappe.utils import flt

from powerpro.controllers.pdf_manager import pdf_manipulator as pdf_manager 
from powerpro.controllers.pdf_manager import signature_helper as signature_helper


PAYLOAD_CANVAS_REQUIRED_FIELDS = (
	"codigo_html",
	"codigo_css",
	"ancho_pdf",
	"alto_pdf",
	"ancho_specs",
	"orientation",
	"margin_top",
	"margin_right",
	"margin_bottom",
	"margin_left",
)

DEFAULT_PAYLOAD_SAFETY = {
	"strict_schema": False,
	"validate_pdf": False,
	"allow_template_functions": True,
	"allow_frappe_proxy": False,
	"enforce_canvas_limits": False,
	"sanitize_html_css": False,
}

SCRIPT_TAG_RE = re.compile(r"<script\b[^<]*(?:(?!</script>)<[^<]*)*</script>", re.IGNORECASE)


@frappe.whitelist()
def generate_pdf_for_printcard(canvas=None, printcard=None, pdf_path=None):
	if not printcard:
		frappe.throw("You must specify a PrintCard to generate the PDF")

	pc = get_princard(printcard)

	filepath = get_file_path(pc.archivo)

	width, height = pdf_manager.get_pdf_dimensions(filepath)

	# frappe.respond_as_web_page(
	# 	title="Generando PDF",
	# 	html=f"""
	# 		width {width} x {height})
	# 	""",
	# )
	# return

	if not canvas:
		canvas = get_best_canvas(width, height)


	if not canvas:
		frappe.respond_as_web_page(
			title="Canvas no encontrado",
			html=f"""
				El Archivo adjunto al PrintCard > {printcard} tiene una dimensión
				no esperada de {flt(width, 3)} x {flt(height, 3)} pulgadas y no se encontró un Canvas que
				coincida con dicha dimensión. Por favor, contacte al administrador del sistema.
				""",
			indicator_color="red",
			http_status_code=404,
			fullpage=True,
		)

		return


	cv = get_canvas(canvas)

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

	if pdf_path:
		# unique_filename = f"{uuid.uuid4()}.pdf"

		unique_filename = get_unique_filename(pc.name, pc.cliente)

		path = f"/files/{unique_filename}"

		with open(
			get_file_path(path), "wb"
		) as f:
			f.write(output.getvalue())
		
		return path

	# Set the response to download the PDF
	frappe.local.response.filename = "{name}.pdf".format(name=printcard.replace(" ", "-").replace("/", "-"))
	# frappe.local.response.filecontent = pdf_buffer.getvalue()
	frappe.local.response.filecontent = output.getvalue()
	frappe.local.response.type = "pdf"


@frappe.whitelist()
def generate_pdf_from_payload(payload=None):
	"""Generate a PrintCard PDF from request payload only (no PrintCard/Canvas records required)."""
	try:
		payload_data = _coerce_payload_dict(payload)
		decoded_pdf = _decode_pdf_base64(payload_data.get("pdf_base64"))
		doc_data = payload_data.get("doc") or {}
		canvas_data = payload_data.get("canvas") or {}
		ink_colors = payload_data.get("ink_colors") or {}
		lookups = payload_data.get("lookups") or {}
		options = payload_data.get("options") or {}
		safety = _get_payload_safety(payload_data.get("safety"))

		_validate_payload_schema(payload_data, canvas_data, safety)

		if safety.get("validate_pdf"):
			pdf_manager.get_pdf_dimensions(decoded_pdf)

		output_pdf = _render_payload_pdf(
			pdf_content=decoded_pdf,
			doc_data=doc_data,
			canvas_data=canvas_data,
			ink_colors=ink_colors,
			lookups=lookups,
			safety=safety,
		)

		filename = _get_payload_filename(doc_data, options)
		return_mode = options.get("return_mode", "base64")
		if return_mode == "inline":
			frappe.local.response.filename = filename
			frappe.local.response.filecontent = output_pdf
			frappe.local.response.type = "pdf"
			return

		return {
			"ok": True,
			"pdf_base64": base64.b64encode(output_pdf).decode("utf-8"),
			"filename": filename,
		}
	except frappe.ValidationError as err:
		return _payload_error("VALIDATION_ERROR", str(err))
	except Exception as err:
		frappe.log_error(frappe.get_traceback(), "generate_pdf_from_payload failed")
		return _payload_error("INTERNAL_ERROR", str(err))


def _payload_error(code, message, details=None):
	return {
		"ok": False,
		"error": {
			"code": code,
			"message": message,
			"details": details or {},
		},
	}


def _coerce_payload_dict(payload):
	if isinstance(payload, str) and payload.strip():
		payload = frappe.parse_json(payload)

	if not payload:
		payload = frappe.form_dict.get("payload")
		if isinstance(payload, str) and payload.strip():
			payload = frappe.parse_json(payload)

	if not payload:
		request = getattr(frappe, "request", None)
		if request and request.data:
			request_data = request.data.decode("utf-8") if isinstance(request.data, bytes) else request.data
			payload = frappe.parse_json(request_data)

	if not isinstance(payload, dict):
		frappe.throw("Invalid payload. Expected a JSON object.")

	return payload


def _decode_pdf_base64(pdf_base64):
	if not pdf_base64 or not isinstance(pdf_base64, str):
		frappe.throw("The 'pdf_base64' field is required.")

	if "," in pdf_base64 and pdf_base64.strip().startswith("data:"):
		pdf_base64 = pdf_base64.split(",", 1)[1]

	try:
		return base64.b64decode(pdf_base64, validate=True)
	except (ValueError, binascii.Error) as err:
		frappe.throw(f"Invalid 'pdf_base64' value: {err}")


def _get_payload_safety(safety):
	payload_safety = safety or {}
	if not isinstance(payload_safety, dict):
		frappe.throw("The 'safety' field must be an object.")
	return {**DEFAULT_PAYLOAD_SAFETY, **payload_safety}


def _validate_payload_schema(payload_data, canvas_data, safety):
	required_root = ("pdf_base64", "doc", "canvas")
	missing_root = [key for key in required_root if key not in payload_data]
	if missing_root:
		frappe.throw(f"Missing required payload fields: {', '.join(missing_root)}")

	if not isinstance(payload_data.get("doc"), dict):
		frappe.throw("The 'doc' field must be an object.")

	if not isinstance(canvas_data, dict):
		frappe.throw("The 'canvas' field must be an object.")

	missing_canvas = [field for field in PAYLOAD_CANVAS_REQUIRED_FIELDS if field not in canvas_data]
	if missing_canvas:
		frappe.throw(f"Missing required canvas fields: {', '.join(missing_canvas)}")

	if safety.get("strict_schema"):
		allowed_root = {"pdf_base64", "doc", "canvas", "ink_colors", "lookups", "options", "safety"}
		unknown_root = sorted(set(payload_data) - allowed_root)
		if unknown_root:
			frappe.throw(f"Unknown payload fields when strict_schema is enabled: {', '.join(unknown_root)}")

	if safety.get("enforce_canvas_limits"):
		for dimension_field in ("ancho_pdf", "alto_pdf"):
			if flt(canvas_data.get(dimension_field)) <= 0:
				frappe.throw(f"Canvas field '{dimension_field}' must be greater than zero.")


def _render_payload_pdf(pdf_content, doc_data, canvas_data, ink_colors, lookups, safety):
	doc_ctx = frappe._dict(doc_data)
	canvas_ctx = frappe._dict(canvas_data)
	html_template = canvas_ctx.codigo_html or ""
	css_template = canvas_ctx.codigo_css or ""

	if safety.get("sanitize_html_css"):
		html_template = SCRIPT_TAG_RE.sub("", html_template)
		css_template = SCRIPT_TAG_RE.sub("", css_template)

	render_context = {
		"doc": doc_ctx,
		"canvas": canvas_ctx,
	}

	if safety.get("allow_template_functions"):
		render_context.update({
			"get_ink_color": _ink_color_from_payload(ink_colors),
			"get_constrast_of_ink_color": _ink_contrast_from_payload(ink_colors),
		})

	if safety.get("allow_frappe_proxy"):
		render_context["frappe"] = frappe._dict({
			"get_value": _payload_get_value(lookups),
		})

	html = frappe.render_template(f"""
		<div>
			{html_template}
			<style>
				{css_template}
				@page {{
					size: {canvas_ctx.ancho_pdf}in {canvas_ctx.alto_pdf}in;
					margin: {canvas_ctx.margin_top}in {canvas_ctx.margin_right}in {canvas_ctx.margin_bottom}in {canvas_ctx.margin_left}in;
				}}
			</style>
		</div>
	""", render_context)

	pdf_buffer = io.BytesIO()
	HTML(string=html).write_pdf(pdf_buffer)
	pdf_buffer.seek(0)

	output = pdf_manager.render_pdf_on_template(pdf_buffer, pdf_content, canvas=canvas_ctx)
	return output.getvalue()


def _payload_get_value(lookups):
	lookups = lookups if isinstance(lookups, dict) else {}

	def _get_value(doctype, name, fieldname):
		if not doctype or not name or not fieldname:
			return None
		doctype_rows = lookups.get(doctype, {})
		row = doctype_rows.get(name, {}) if isinstance(doctype_rows, dict) else {}
		if not isinstance(row, dict):
			return None
		return row.get(fieldname)

	return _get_value


def _ink_color_from_payload(ink_colors):
	palette = ink_colors if isinstance(ink_colors, dict) else {}

	def _get_ink_color(ink_color_id):
		return palette.get(ink_color_id) or "#ffffff"

	return _get_ink_color


def _ink_contrast_from_payload(ink_colors):
	get_ink = _ink_color_from_payload(ink_colors)

	def _get_contrast_color(ink_color_id):
		return get_contrast(get_ink(ink_color_id))

	return _get_contrast_color


def _get_payload_filename(doc_data, options):
	output_filename = (options or {}).get("output_filename")
	if output_filename:
		return output_filename

	name = (doc_data or {}).get("name") or uuid.uuid4().hex
	return f"{name}".replace("/", "-").replace(" ", "-") + ".pdf"


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
		"name",
		"ancho_pdf",
		"alto_pdf",
		"ancho_specs",
		"orientation",
	]):
		# if canvas.orientation == "Portrait":
		if canvas.ancho_pdf < canvas.alto_pdf: # Vertical (Portrait)
			width = canvas.ancho_pdf
			height = canvas.alto_pdf - canvas.ancho_specs
		else: # Horizontal (Landscape)
			height = canvas.alto_pdf
			width = canvas.ancho_pdf - canvas.ancho_specs

		out.append(
			(canvas.name, width, height, "Portrait" if height > width else "Landscape")
		)

	return out


def get_minimum_canvas_margin():
	doctype = "PreProIGC Settings"
	fieldname = "minimum_canvas_margin"

	return frappe.db.get_single_value(doctype, fieldname)


def get_best_canvas(pdf_width, pdf_height, raise_if_empty=False) -> str:
	canvas_list = get_canvas_list_without_ancho_specs()

	if not canvas_list:
		if raise_if_empty:
			frappe.throw("No PrintCard Canvas documents found.")
		return None

	minimum_canvas_margin = get_minimum_canvas_margin()

	out = pdf_manager.select_best_canvas(
		pdf_width, pdf_height, canvas_list, minimum_canvas_margin
	)

	if out:
		return out[0] # Return the canvas name
	
	return None


@frappe.whitelist()
def sign_pdf_with_base64(printcard_id) -> bool:
	"""Sign the PDF of a PrintCard with a Base64-encoded signature."""
	frappe.enqueue(
		_sign_pdf_with_base64,
		printcard_id=printcard_id,
		enqueue_after_commit=True,
	)

def _sign_pdf_with_base64(printcard_id) -> bool:
	# Get the PrintCard
	printcard = get_princard(printcard_id)

	# Get the signature from the PrintCard
	signature = printcard.firma_cliente
	
	# Get the file path of the PDF
	ofilepath = get_file_path(printcard.archivo)
	filepath = get_file_path(printcard.printcard_file)

	signed_pdf_filename = get_unique_filename(printcard.name, printcard.cliente, suffix="firmado")
	
	width, height = pdf_manager.get_pdf_dimensions(ofilepath)

	canvas = get_canvas(
		get_best_canvas(width, height, raise_if_empty=True)
	)

	# Generate a unique filename for the signed PDF
	signed_pdf_path = f"/files/{signed_pdf_filename}"
	if frappe.session.user == "Administrator":
		signed_pdf_path = f"/files/{canvas.name}-{uuid.uuid4()}.pdf"
	
	# Sign the PDF
	signed = signature_helper.sign_pdf_with_base64(
		pdf_path=filepath,
		base64_signature=signature,
		output_path=get_file_path(signed_pdf_path),
		x=canvas.signature_x_position * 72,
		y=canvas.signature_y_position * 72,
		width=canvas.signature_width * 72,
		height=canvas.signature_height * 72,
		date_x_pos=canvas.date_x_position,
		date_y_pos=canvas.date_y_position,
		date_size=canvas.font_size,
		date_color=convert_hex_to_rgb(canvas.date_font_color),
	)

	if signed:
		printcard.printcard_file_signed = signed_pdf_path
		printcard.save()

		frappe.msgprint(
			f"El PrintCard {printcard.name} ha sido firmado correctamente.",
			indicator="green",
			alert=True,
		)
	else:
		frappe.throw(
			"Ha ocurrido un error al firmar el PrintCard. Por favor, intente de nuevo."
		)


def get_princard(name: str) -> "document.Document":
	doctype = "PrintCard"
	if not frappe.db.exists(doctype, name):
		frappe.throw(f"The PrintCard {name} does not exist.")

	return frappe.get_doc(doctype, name)


def get_canvas(name: str) -> "document.Document":
	if not name:
		frappe.throw("You must specify a PrintCard Canvas to get.")

	doctype = "PrintCard Canvas"
	return frappe.get_doc(doctype, name)


def get_unique_filename(princard_id: str, customer: str, suffix=None) -> str:
	repl_customer = f"{customer} - "

	filename = f"{princard_id.replace(repl_customer, '')}"
	if suffix:
		filename = f"{filename}_{suffix}"

	return f"{filename}.pdf"


def convert_hex_to_rgb(hex_color: str) -> tuple:
	"""Convert a hexadecimal color to an RGB tuple."""
	hex_color = hex_color.lstrip("#")  # Remove the "#" if present
	r, g, b = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

	return r, g, b
