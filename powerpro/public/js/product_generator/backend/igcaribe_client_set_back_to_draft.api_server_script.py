# Source Server Script: igcaribe.client.set_back_to_draft
# API Method: igcaribe.client.set_back_to_draft
# Site: igcaribe.fortabs.com

# Restrict access to users with the "System Manager" role
only_for = "System Manager"
if not frappe.db.exists(
    "Has Role",
    {
        "parent": frappe.user,  # current user
        "role": only_for,  # required role
    },
):
    # Throw an error if the user doesn't have the required role
    frappe.throw(f"This Action is only allowed for {only_for!r}")

# Retrieve form inputs from the request
doctype = frappe.form_dict.doctype  # e.g., "Sales Invoice"
name = frappe.form_dict.name  # name or ID of the document

# optional flag to reset the status field
with_status = (
    frappe.form_dict.with_status
    and frappe.form_dict.with_status != "false"
    and frappe.form_dict.with_status != "0"
)

# Validate that if 'with_status' is requested, the doc has a 'status' attribute
# if with_status and not hasattr(doc, "status"):
meta = frappe.get_meta(doctype)

if with_status and not meta.get_field("status"):
    frappe.throw(f"El DocType > {doctype} no tiene un campo llamado 'status'")

# Load the document instance
doc = frappe.get_doc(doctype, name)

doc.flags.for_reload = True

# Ensure the document is submitted (docstatus == 1) before reverting to draft
if doc.docstatus != 1:
    frappe.throw(
        f"El Documento '{doctype} > {name}' no se encuentra en un estado para ser enviado a Borrador"
    )

# Cancel the document to revert it from submitted state
doc.cancel()

# Reload the document from the database to refresh its data
doc.reload()

# Manually reset docstatus to 0 (Draft)
doc.docstatus = 0
doc.set_docstatus()  # Update any internal status indicators based on docstatus

# If requested, reset the document's custom status field to "Draft"
if with_status:
    doc.status = "Draft"

# Update the document record in the database with the new values
doc.db_update_all()
