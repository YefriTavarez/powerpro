# Source Server Script: get_product_hash
# API Method: get_product_hash
# Site: igcaribe.fortabs.com

docname = frappe.form_dict.get("docname")

if not docname:
    frappe.throw("Falta el nombre del documento")

doc = frappe.get_doc("Product Generator", docname)

# Recalcular el hash real
doc.run_method("validate")  # Calcula el hash en el servidor
frappe.db.commit()  # Guarda el hash si se actualizó

# Devuelve el hash en la estructura que espera frappe.call().message
frappe.response["message"] = {"product_hash": doc.product_hash or ""}
