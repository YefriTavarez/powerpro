# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import pyqrcode
from io import BytesIO
import frappe
from frappe import whitelist
from werkzeug.wrappers import Response


@whitelist(allow_guest=True)
def generate_qr():
    """
    Returns a QR code image in binary (PNG) format based on a URL passed as a query parameter.
    Example usage: /api/method/your_app.api.generate_qr_code?value=APR-0001
    """
    value = frappe.form_dict.get("value")

    if not value:
        frappe.throw("Missing 'value' parameter in query string.")

    # Generate QR code
    qr = pyqrcode.create(value)

    # Convert image to binary buffer
    buffer = BytesIO()
    qr.png(buffer, scale=6, quiet_zone=4)  # Customize scale & border if needed
    buffer.seek(0)

    # Return raw image response
    return Response(buffer.getvalue(), content_type='image/png')
