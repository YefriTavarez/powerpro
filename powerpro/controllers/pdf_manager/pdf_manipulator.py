# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

# import fitz  # PyMuPDF
# import io

from pypdf import PdfReader, PdfWriter, PageObject
import io

def render_pdf_on_template(outer_pdf_buffer, inner_pdf_path):
    """
    Embed a PDF into another using pypdf, with scaling and positioning applied manually.

    Parameters:
        outer_pdf_buffer (io.BytesIO): Template PDF as a BytesIO object.
        inner_pdf_path (str): Path to the PDF to be embedded.

    Returns:
        io.BytesIO: BytesIO buffer containing the resulting PDF.
    """
    # Load the template and embedded PDFs
    outer_pdf = PdfReader(outer_pdf_buffer)
    inner_pdf = PdfReader(inner_pdf_path)
    writer = PdfWriter()

    # Assume the template has a single page
    outer_page = outer_pdf.pages[0]

    # Get dimensions of the template
    template_width = 26 * 72  # 26 inches to points
    template_height = 24 * 72  # 24 inches to points
    margin = 7 * 72  # Right margin in points
    render_width = 19 * 72  # Render area width
    render_height = 24 * 72  # Render area height

    # Get the first page of the embedded PDF
    inner_page = inner_pdf.pages[0]
    inner_page_width = inner_page.mediabox.width
    inner_page_height = inner_page.mediabox.height

    # Calculate scaling factor to fit the embedded PDF within the render area
    # scale_x = render_width / inner_page_width
    # scale_y = render_height / inner_page_height
    # scale = min(scale_x, scale_y)
    scale = 1

    # Calculate position to center the embedded PDF in the render area
    scaled_width = inner_page_width * scale
    scaled_height = inner_page_height * scale
    # left = template_width - margin - render_width + (render_width - scaled_width) / 2


    center_of_template = (template_width / 2) + margin
    center_of_inner_pdf = inner_page_width / 2

    left = center_of_template - center_of_inner_pdf

    bottom = (template_height - scaled_height) / 2

    # Create a new page with the scaled and positioned embedded content
    embedded_page = PageObject.create_blank_page(
        width=template_width,
        height=template_height,
    )
    embedded_page.merge_page(inner_page)
    embedded_page.add_transformation(
        [scale, 0, 0, scale, left, bottom]
    )
    # Apply a 180-degree rotation to the embedded content
    embedded_page.add_transformation(
        [1, 0, 0, -1, 0, template_height]
    )

    # Merge the embedded content onto the template page
    outer_page.merge_page(embedded_page)

    # Add the modified page to the writer
    writer.add_page(outer_page)

    # Save the output to a BytesIO buffer
    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)

    return output_buffer
