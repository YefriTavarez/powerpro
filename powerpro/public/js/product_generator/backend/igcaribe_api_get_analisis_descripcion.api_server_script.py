# Source Server Script: igcaribe.api.get_analisis_descripcion
# API Method: igcaribe.api.get_analisis_descripcion
# Site: igcaribe.fortabs.com

doc = frappe.get_doc("Analisis de Arte Settings", "Analisis de Arte Settings")
template_codigo = doc.codigo or ""
template_titulo = doc.product_title or ""

data = frappe.form_dict.copy()


def parse_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return False


# Asegurar valores planos en todos los campos del form_dict
for key, value in data.items():
    if isinstance(value, dict):
        data[key] = frappe.as_json(value)
    elif isinstance(value, list):
        data[key] = ", ".join(map(str, value))

# Normalizar campos checkbox
checkbox_fields = [
    "requiere_troquelado",
    "requiere_laminado",
    "requiere_barnizado",
    "requiere_pegado",
    "requiere_impresion",
    "requiere_acabado_especial",
    "requiere_cinta_doble_cara",
]

for field in checkbox_fields:
    data[field] = parse_bool(data.get(field))

# Renderizado seguro
try:
    resultado_codigo = frappe.render_template(template_codigo, data).strip()
    resultado_titulo = frappe.render_template(template_titulo, data).strip()

    frappe.response["message"] = {
        "codigo": resultado_codigo,
        "product_title": resultado_titulo,
    }

except Exception as e:
    frappe.log_error(frappe.get_traceback(), "Error renderizando templates Jinja")
    frappe.response["message"] = f"ERROR: {str(e)}"
