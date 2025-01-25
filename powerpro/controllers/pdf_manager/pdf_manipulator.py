# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

# import fitz  # PyMuPDF
# import io

from pypdf import PdfReader, PdfWriter, PageObject
import io

def render_pdf_on_template(template_buffer, embed_pdf_path):
    """
    Embed a PDF into another using pypdf, with scaling and positioning applied manually.

    Parameters:
        template_buffer (io.BytesIO): Template PDF as a BytesIO object.
        embed_pdf_path (str): Path to the PDF to be embedded.

    Returns:
        io.BytesIO: BytesIO buffer containing the resulting PDF.
    """
    # Load the template and embedded PDFs
    template_reader = PdfReader(template_buffer)
    embed_reader = PdfReader(embed_pdf_path)
    writer = PdfWriter()

    # Assume the template has a single page
    template_page = template_reader.pages[0]

    # Get dimensions of the template
    template_width = 26 * 72  # 26 inches to points
    template_height = 24 * 72  # 24 inches to points
    margin = 7 * 72  # Right margin in points
    render_width = 19 * 72  # Render area width
    render_height = 24 * 72  # Render area height

    # Get the first page of the embedded PDF
    embed_page = embed_reader.pages[0]
    embed_width = embed_page.mediabox.width
    embed_height = embed_page.mediabox.height

    # Calculate scaling factor to fit the embedded PDF within the render area
    scale_x = render_width / embed_width
    scale_y = render_height / embed_height
    scale = min(scale_x, scale_y)

    # Calculate position to center the embedded PDF in the render area
    scaled_width = embed_width * scale
    scaled_height = embed_height * scale
    left = template_width - margin - render_width + (render_width - scaled_width) / 2
    bottom = (render_height - scaled_height) / 2

    # Create a new page with the scaled and positioned embedded content
    embedded_page = PageObject.create_blank_page(
        width=template_width,
        height=template_height,
    )
    embedded_page.merge_page(embed_page)
    embedded_page.add_transformation(
        [scale, 0, 0, scale, left, bottom]
    )
    # Apply a 180-degree rotation to the embedded content
    embedded_page.add_transformation(
        [1, 0, 0, -1, 0, template_height]
    )

    # Merge the embedded content onto the template page
    template_page.merge_page(embedded_page)

    # Add the modified page to the writer
    writer.add_page(template_page)

    # Save the output to a BytesIO buffer
    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)

    return output_buffer

# # Example Usage
# template_buffer = io.BytesIO()

# # Load the template PDF into the buffer (e.g., from a file)
# with open("template.pdf", "rb") as f:
#     template_buffer.write(f.read())
# template_buffer.seek(0)

# # Path to the embedded PDF
# embed_pdf_path = "embed.pdf"

# # Generate the output PDF buffer
# output_pdf_buffer = render_pdf_on_template(template_buffer, embed_pdf_path)

# # Save the resulting PDF to a file (optional, for testing)
# with open("output.pdf", "wb") as f:
#     f.write(output_pdf_buffer.read())

def v0__render_pdf_on_template(template_buffer, embed_pdf_path):
    """
    Renders one PDF onto a specific section of a template PDF provided as a BytesIO buffer
    and returns the output as a BytesIO buffer.
    
    Parameters:
        template_buffer (io.BytesIO): In-memory buffer of the template PDF.
        embed_pdf_path (str): Path to the PDF to be rendered on the template.
    
    Returns:
        io.BytesIO: In-memory buffer containing the modified PDF.
    """
    # Define the template size and render area dimensions
    template_width = 26 * 72  # Convert inches to points (1 inch = 72 points)
    template_height = 24 * 72
    margin = 7 * 72  # Right margin in points
    render_width = 19 * 72  # Render area width
    render_height = 24 * 72  # Render area height

    # Open the template and embedding PDFs
    template_pdf = fitz.open(stream=template_buffer, filetype="pdf")
    embed_pdf = fitz.open(embed_pdf_path)

    # Render the first page of the embed PDF as an image
    embed_page = embed_pdf[0]
    pix = embed_page.get_pixmap()

    # Calculate the scaling to fit the embed PDF within the render area
    scale_x = render_width / pix.width
    scale_y = render_height / pix.height
    scale = min(scale_x, scale_y)  # Uniform scaling

    # Compute the position to center the PDF in the render area
    embed_width = pix.width * scale
    embed_height = pix.height * scale
    left = template_width - margin - render_width + (render_width - embed_width) / 2
    top = (render_height - embed_height) / 2
    right = left + embed_width
    bottom = top + embed_height

    # Insert the image into the template
    page = template_pdf[0]  # Use the first page of the template
    page.insert_image(fitz.Rect(left, top, right, bottom), pixmap=pix)

    # Save the output to a BytesIO buffer
    output_buffer = io.BytesIO()
    template_pdf.save(output_buffer)

    # Close the documents
    template_pdf.close()
    embed_pdf.close()

    # Reset the buffer position to the beginning before returning
    output_buffer.seek(0)
    return output_buffer

# # Example usage
# template_buffer = io.BytesIO()  # Replace with actual buffer containing your template PDF
# embed_pdf_path = "embed.pdf"

# # Load a template PDF into the buffer (Example: reading from a file)
# with open("template.pdf", "rb") as f:
#     template_buffer.write(f.read())

# # Reset the buffer position to the beginning before use
# template_buffer.seek(0)

# # Generate the output PDF buffer
# output_pdf_buffer = render_pdf_on_template(template_buffer, embed_pdf_path)

# # Example: Write the buffer to a file (optional, for testing)
# with open("output.pdf", "wb") as f:
    f.write(output_pdf_buffer.read())