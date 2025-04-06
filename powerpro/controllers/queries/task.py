# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe
from frappe.desk.reportview import get_filters_cond

@frappe.whitelist()
def get_user_tasks(doctype, txt, searchfield, start, page_len, filters):
    """
    Retrieve tasks assigned to the current user unless the user is a project manager.
    """
    filtrs = []

    if not has_role(
        get_project_manager()
    ):
        filters["responsible"] = frappe.session.user

    if user := filters["responsible"]:
        filtrs.append([ "Task Responsible", "user", "=", user ])

        del filters["responsible"]

    searchstr = f"%{txt}%" if txt else "%%"
    if searchstr:
        filters[searchfield] = ["like", searchstr]

    for fieldname, value in filters.items():
        if isinstance(value, str):
            filtrs.append(["Task", fieldname, "=", value])
        elif isinstance(value, list):
            args = ["Task", fieldname]
            args.extend(value)
            filtrs.append(args)

    return frappe.get_all(
        "Task",
        filters=filtrs,
        fields=["`tabTask`.name", "`tabTask`.subject", "`tabTask`.status"],
        order_by="`tabTask`.modified desc",
        limit_start=start,
        limit_page_length=page_len,
        as_list=True,
    )



def get_project_manager() -> str:
    """Get the project manager from the settings."""
    settings = frappe.get_single("Projects Settings")

    return settings.project_manager or "System Manager"


def has_role(role: str) -> bool:
    """Check if the user has a specific role."""
    return role in frappe.get_roles()
