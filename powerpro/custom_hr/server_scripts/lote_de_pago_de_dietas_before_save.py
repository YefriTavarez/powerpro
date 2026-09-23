if not doc.flags.get('dieta_service'):
    frappe.throw('Utilice los diálogos de Dietas.', frappe.PermissionError)
