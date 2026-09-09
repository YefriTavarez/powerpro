import frappe

no_cache = 1


def get_context(context):
    if frappe.session.user == 'Guest':
        frappe.throw('Inicie sesión para solicitar una dieta.', frappe.PermissionError)
    context.title = 'Mis solicitudes de dieta'
