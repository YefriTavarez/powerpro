# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe


def printcard_query_conditions(user, doctype=None):
    # empty string for System Users
    
    user_type = frappe.db.get_value("User", user, "user_type")
    if user_type != "Website User":
        return ""

    return f"""
        EXISTS (
            SELECT 1
            FROM `tabUsuario Aprobacion`
            WHERE `tabUsuario Aprobacion`.`parent` = `tabPrintCard`.`name`
            AND `tabUsuario Aprobacion`.`user` = "{user}"
        )
    """
