import frappe


def execute():
    """Patch script to rename all items using the new naming approach."""
    items = frappe.get_all("Item", fields=["name", "custom_item_group_1", "custom_item_group_2", "custom_item_group_3", "custom_item_group_4", "custom_item_group_5"])

    for item in items:
        new_name = get_new_item_name(item)
        if new_name and new_name != item.name:
            frappe.rename_doc("Item", item.name, new_name, force=True)


def get_new_item_name(item):
    """Generate the new name for an item based on its custom item groups."""
    for field in reversed([
        "custom_item_group_1",
        "custom_item_group_2",
        "custom_item_group_3",
        "custom_item_group_4",
        "custom_item_group_5",
    ]):
        group_name = item.get(field)
        if group_name:
            group_number = frappe.db.get_value("Item Group", group_name, "item_group_number")
            if not group_number:
                frappe.throw(f"El grupo de artículos '{group_name}' no tiene un número de grupo de artículos asignado.")

            existing = frappe.db.sql_list("""
                SELECT name FROM `tabItem`
                WHERE name LIKE %s
            """, (f"{group_number}-%",))

            used = [int(code.split("-")[1]) for code in existing if "-" in code and code.split("-")[1].isdigit()]
            next_number = max(used or [0]) + 1

            return f"{group_number}-{str(next_number).zfill(3)}"

    frappe.throw("No se ha definido ningún grupo de artículos (1 a 5) para este artículo.")
