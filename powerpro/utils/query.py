import frappe


def customer_query_conditions(user):
    settings = get_igc_settings()

    if not user: 
        user = frappe.session.user

    if not settings.hide_informal_customers:
        return ""

    return "`tabCustomer`.informal_customer = 0"


def quotation_query_conditions(user):
    settings = get_igc_settings()

    if not user: 
        user = frappe.session.user

    if not settings.hide_informal_customers:
        return ""

    informal_customers = get_informal_customers()

    if informal_customers:
        informal_customers = ", ".join(f"'{customer[0]}'" for customer in informal_customers)
        return f"`tabQuotation`.party_name Not In ({informal_customers})"
    else:
        return ""


def sales_order_query_conditions(user):
    settings = get_igc_settings()

    if not user: 
        user = frappe.session.user

    if not settings.hide_informal_customers:
        return ""

    informal_customers = get_informal_customers()

    if informal_customers:
        informal_customers = ", ".join(f"'{customer[0]}'" for customer in informal_customers)
        return f"`tabSales Order`.customer Not In ({informal_customers})"
    else:
        return ""


def sales_invoice_query_conditions(user):
    settings = get_igc_settings()

    if not user: 
        user = frappe.session.user

    if not settings.hide_informal_customers:
        return ""

    informal_customers = get_informal_customers()

    if informal_customers:
        informal_customers = ", ".join(f"'{customer[0]}'" for customer in informal_customers)
        return f"`tabSales Invoice`.customer Not In ({informal_customers})"
    else:
        return ""


def payment_entry_query_conditions(user):
    settings = get_igc_settings()

    if not user: 
        user = frappe.session.user

    if not settings.hide_informal_customers:
        return ""

    informal_customers = get_informal_customers()

    if informal_customers:
        informal_customers = ", ".join(f"'{customer[0]}'" for customer in informal_customers)
        return f"`tabPayment Entry`.party Not In ({informal_customers})"
    else:
        return ""


def delivery_note_query_conditions(user):
    settings = get_igc_settings()

    if not user: 
        user = frappe.session.user

    if not settings.hide_informal_customers:
        return ""

    informal_customers = get_informal_customers()

    if informal_customers:
        informal_customers = ", ".join(f"'{customer[0]}'" for customer in informal_customers)
        return f"`tabDelivery Note`.customer Not In ({informal_customers})"
    else:
        return ""


def asset_maintenance_log_query_conditions(user):
    if not user: 
        user = frappe.session.user

    allowed_roles = [
        "System Manager",
        "Encargado Mantenimiento",
    ]

    if frappe.get_roles(user) and any(role in allowed_roles for role in frappe.get_roles(user)):
        return

    return f"`tabAsset Maintenance Log`.task_assignee_email = {user!r} or `tabAsset Maintenance Log`.maintenance_manager = {user!r}"


def todo_query_conditions(user):
    if not user: 
        user = frappe.session.user

    allowed_roles = [
        "System Manager",
        "Encargado Mantenimiento",
    ]

    user_roles = frappe.get_roles(user)

    if user_roles and any(role in allowed_roles for role in user_roles):
        return

    return f"`tabToDo`.allocated_to = {user!r} or `tabToDo`.maintenance_manager = {user!r}"


def get_informal_customers():
    data = frappe.db.sql("""
        Select
            name
        From
            tabCustomer
        Where
            informal_customer = 1
    """, as_list=True)

    return data


def get_igc_settings():
    doctype = "IGC Settings"
    return frappe.get_single(doctype)