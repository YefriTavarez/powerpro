# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

# import fitz  # PyMuPDF
# import io
from pypdf import PdfReader, PdfWriter, PageObject, Transformation
from io import BytesIO

def render_pdf_on_template(pdf1_buffer, pdf2_path):
    # Leer PDF1 (template) desde el buffer
    pdf1 = PdfReader(pdf1_buffer)
    pdf1_page = pdf1.pages[0]
    pdf1_width = float(pdf1_page.mediabox.width)  # En puntos
    pdf1_height = float(pdf1_page.mediabox.height)  # En puntos
    
    # Leer PDF2 (contenido a sobreponer) desde el archivo
    pdf2 = PdfReader(pdf2_path)
    pdf2_page = pdf2.pages[0]
    pdf2_width = float(pdf2_page.mediabox.width)  # En puntos
    pdf2_height = float(pdf2_page.mediabox.height)  # En puntos
    
    # Definir márgenes en pulgadas y convertirlos a puntos
    left_margin = 7.5 * 72  # 7 pulgadas = 7 * 72 puntos
    right_margin = 0.5 * 72  # 0.5 pulgadas = 0.5 * 72 puntos
    top_margin = 0.5 * 72  # 0.5 pulgadas = 0.5 * 72 puntos
    bottom_margin = 0.5 * 72  # 0.5 pulgadas = 0.5 * 72 puntos
    
    # Calcular ancho y altura disponibles para PDF2
    available_width = pdf1_width - left_margin - right_margin  # Ancho disponible en puntos
    available_height = pdf1_height - top_margin - bottom_margin  # Altura disponible en puntos

    # Calcular las coordenadas para posicionar PDF2 dentro del área restante
    x_offset = left_margin + (available_width - pdf2_width) / 2  # Centrar horizontalmente en puntos
    y_offset = bottom_margin + (available_height - pdf2_height) / 2  # Centrar verticalmente en puntos

    # Crear un buffer para el PDF combinado
    output_buffer = BytesIO()
    writer = PdfWriter()
    
    # Crear una página combinada
    combined_page = PageObject.create_blank_page(width=pdf1_width, height=pdf1_height)
    combined_page.merge_page(pdf1_page)  # Agregar PDF1 como base

    # Posicionar y combinar PDF2
    pdf2_translated = PageObject.create_blank_page(width=pdf1_width, height=pdf1_height)
    pdf2_translated.merge_page(pdf2_page)
    transformation = Transformation().translate(tx=x_offset, ty=y_offset)  # Aplicar transformación con desplazamiento
    pdf2_translated.add_transformation(transformation)
    combined_page.merge_page(pdf2_translated)  # Combinar ambos
    
    # Agregar la página combinada al escritor
    writer.add_page(combined_page)
    
    # Escribir el PDF resultante en el buffer
    writer.write(output_buffer)
    output_buffer.seek(0)  # Reiniciar el puntero al inicio del buffer
    
    return output_buffer

# from pypdf import PdfReader, PdfWriter, PageObject
# from io import BytesIO

# def v10_render_pdf_on_template(pdf1_buffer, pdf2_path):
#     # Leer PDF1 desde buffer
#     pdf1 = PdfReader(pdf1_buffer)
#     pdf1_page = pdf1.pages[0]
#     pdf1_width = float(pdf1_page.mediabox.width)
#     pdf1_height = float(pdf1_page.mediabox.height)
    
#     # Leer PDF2 desde archivo
#     pdf2 = PdfReader(pdf2_path)
#     pdf2_page = pdf2.pages[0]
#     pdf2_width = float(pdf2_page.mediabox.width)
#     pdf2_height = float(pdf2_page.mediabox.height)
    
#     # Calcular las coordenadas para centrar PDF1 en PDF2
#     x_offset = (pdf2_width - pdf1_width) / 2
#     y_offset = (pdf2_height - pdf1_height) / 2
    
#     # Crear un nuevo PDF combinando ambos contenidos
#     output_buffer = BytesIO()
#     writer = PdfWriter()
    
#     for page in pdf2.pages:
#         # Crear una nueva página combinada con la página base (PDF2)
#         combined_page = PageObject.create_blank_page(width=pdf2_width, height=pdf2_height)
#         combined_page.merge_page(page)  # Página base de PDF2
        
#         # Ajustar la posición de PDF1 sobre PDF2
#         pdf1_page_translated = PageObject.create_blank_page(width=pdf2_width, height=pdf2_height)
#         pdf1_page_translated.merge_page(pdf1_page)
#         pdf1_page_translated.add_transformation([1, 0, 0, 1, x_offset, y_offset])  # Aplicar transformación
#         combined_page.merge_page(pdf1_page_translated)  # Combinar con PDF1
        
#         writer.add_page(combined_page)
    
#     # Escribir el PDF combinado en el buffer
#     writer.write(output_buffer)
#     output_buffer.seek(0)  # Reiniciar el puntero al inicio del buffer
    
#     return output_buffer

# def v0_render_pdf_on_template(outer_pdf_buffer, inner_pdf_path):
#     """
#     Embed a PDF into another using pypdf, with scaling and positioning applied manually.

#     Parameters:
#         outer_pdf_buffer (io.BytesIO): Template PDF as a BytesIO object.
#         inner_pdf_path (str): Path to the PDF to be embedded.

#     Returns:
#         io.BytesIO: BytesIO buffer containing the resulting PDF.
#     """
#     # Load the template and embedded PDFs
#     outer_pdf = PdfReader(outer_pdf_buffer)
#     inner_pdf = PdfReader(inner_pdf_path)
#     writer = PdfWriter()

#     # Assume the template has a single page
#     outer_page = outer_pdf.pages[0]

#     # Get dimensions of the template
#     template_width = 26 * 72  # 26 inches to points
#     template_height = 24 * 72  # 24 inches to points
#     margin = 7.5 * 72  # Right margin in points
#     render_width = 19 * 72  # Render area width
#     render_height = 24 * 72  # Render area height

#     # Get the first page of the embedded PDF
#     inner_page = inner_pdf.pages[0]
#     inner_page_width = inner_page.mediabox.width
#     inner_page_height = inner_page.mediabox.height

#     with open("/home/frappe/yefri-bench/nomellegaunombre.txt", "a") as f:
#         f.write(f"inner_page_width: {inner_page_width}\n")
#         f.write(f"inner_page_height: {inner_page_height}\n")

#     # Calculate scaling factor to fit the embedded PDF within the render area
#     # scale_x = render_width / inner_page_width
#     # scale_y = render_height / inner_page_height
#     # scale = min(scale_x, scale_y)
#     scale = 1

#     # Calculate position to center the embedded PDF in the render area
#     scaled_width = inner_page_width * scale
#     scaled_height = inner_page_height * scale
#     # left = template_width - margin - render_width + (render_width - scaled_width) / 2


#     center_of_template = (template_width / 2) + margin
#     center_of_inner_pdf = inner_page_width / 2

#     left = center_of_template - center_of_inner_pdf

#     bottom = (template_height - scaled_height) / 2

#     # Create a new page with the scaled and positioned embedded content
#     embedded_page = PageObject.create_blank_page(
#         width=template_width + 420,
#         height=template_height + 420,
#     )
#     embedded_page.merge_page(inner_page, over=True)
#     # embedded_page.add_transformation(
#     #     [scale, 0, 0, scale, 0, bottom]
#     # )
#     # # Apply a 180-degree rotation to the embedded content
#     # embedded_page.add_transformation(
#     #     [1, 0, 0, -1, 0, template_height]
#     # )

#     # Merge the embedded content onto the template page
#     outer_page.merge_page(embedded_page)

#     # Add the modified page to the writer
#     writer.add_page(outer_page)

#     # Save the output to a BytesIO buffer
#     output_buffer = io.BytesIO()
#     writer.write(output_buffer)
#     output_buffer.seek(0)

#     return output_buffer
