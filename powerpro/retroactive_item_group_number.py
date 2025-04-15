import frappe
from frappe import _


CATEGORY_RANGES = {
    "Artículos": (1000, 3999),
    "Productos": (4000, 7999),
    "Servicios": (9000, 9999),
}

def retroactively_assign_item_group_numbers():
    """Assign item_group_number to existing Item Groups."""
    item_groups = frappe.get_all("Item Group", fields=["name", "parent_item_group", "item_group_number"])

    for group in item_groups:
        if group.item_group_number:
            continue  # Skip if already assigned

        root_category = get_root_category(group)
        if root_category not in CATEGORY_RANGES:
            continue  # Skip if no range is defined

        start, end = CATEGORY_RANGES[root_category]
        used_numbers = frappe.db.get_all(
            "Item Group",
            filters={"item_group_number": ["between", [start, end]]},
            pluck="item_group_number",
        )

        used_numbers = set(int(num) for num in used_numbers if num.isdigit())

        for number in range(start, end + 1):
            if number not in used_numbers:
                frappe.db.set_value("Item Group", group.name, "item_group_number", f"{number:04d}")
                break


def get_root_category(doc):
    """Traverse up the tree to find the root category."""
    while doc.parent_item_group and (
		doc.parent_item_group != "All Item Groups"
		or doc.parent_item_group != _("All Item Groups")
	):
        doc = frappe.get_doc("Item Group", doc.parent_item_group)
    return doc.name