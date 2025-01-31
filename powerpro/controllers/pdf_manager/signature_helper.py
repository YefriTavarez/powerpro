# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import os
import uuid
import base64
from io import BytesIO

import fitz  # PyMuPDF
from PIL import Image

from frappe import utils


def sign_pdf_with_base64(
    pdf_path,
    base64_signature,
    output_path,
    x=100,
    y=500,
    width=200,
    height=50,
    date_x_pos=1.5,
    date_y_pos=1.5,
    date_size=12,
    date_color=(0, 0, 0),
) -> bool:
    """
    Overlay a Base64-encoded signature onto a PDF with unique file handling.
    Args:
        pdf_path (str): The path to the PDF file to be signed.
        base64_signature (str): The Base64-encoded signature image.
        output_path (str): The path where the signed PDF will be saved.
        x (int, optional): The x-coordinate of the signature's position on the PDF. Defaults to 100.
        y (int, optional): The y-coordinate of the signature's position on the PDF. Defaults to 500.
        width (int, optional): The width of the signature image. Defaults to 200.
        height (int, optional): The height of the signature image. Defaults to 50.
        date_x_pos (float, optional): The x-coordinate position of the date relative to the signature. Defaults to 1.5.
        date_y_pos (float, optional): The y-coordinate position of the date relative to the signature. Defaults to 1.5.
        date_size (int, optional): The font size of the date text. Defaults to 12.
        date_color (tuple, optional): The color of the date text in RGB format. Defaults to (0, 0, 0).
    Returns:
        bool: True if the PDF was signed successfully, False otherwise.
    """

    # Remove the "data:image/png;base64," prefix if it exists
    if base64_signature.startswith("data:image"):
        base64_signature = base64_signature.split(",")[1]

    # Decode the Base64 signature
    signature_data = base64.b64decode(base64_signature)
    
    # Convert to an image (PIL)
    signature_image = Image.open(
        BytesIO(signature_data)
    )
    
    # Generate a unique filename
    unique_filename = f"/tmp/signature_{uuid.uuid4().hex}.png"
    
    # Save the image temporarily
    signature_image.save(unique_filename)

    try:
        # Open the existing PDF
        doc = fitz.open(pdf_path)
        page = doc[0]  # Assume signing on the first page
        
        # Define where the signature should be placed
        rect = fitz.Rect(x, y, x + width, y + height)
        
        # Insert the signature image
        page.insert_image(rect, filename=unique_filename)

        page.insert_text(
            (
                x - (date_x_pos * 72),
                y + (height / date_y_pos)
            ), utils.today(), fontsize=date_size, color=date_color
        )

        # Save the new signed PDF
        doc.save(output_path)
        doc.close()

        return True
        # print(f"Signed PDF saved as: {output_path}")
    except Exception as e:
        return False

    finally:
        # Delete the temporary signature image
        if os.path.exists(unique_filename):
            os.remove(unique_filename)

# # Example Base64 string (Replace this with actual data from your database)
# sample_base64_signature = "iVBORw0KGgoAAAANSUhEUgAA..."  # Truncated example

# # Example usage
# sign_pdf_with_base64("input.pdf", sample_base64_signature, "signed_output.pdf", x=100, y=500, width=200, height=50)