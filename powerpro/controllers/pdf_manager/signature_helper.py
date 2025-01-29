# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import os
import uuid
import base64
from io import BytesIO

import fitz  # PyMuPDF
from PIL import Image


def sign_pdf_with_base64(
    pdf_path, base64_signature, output_path, x=100, y=500, width=200, height=50
):
    """Overlay a Base64-encoded signature onto a PDF with unique file handling."""

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