# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe

@frappe.whitelist()
def get_art_list(arte_id):
    """Fetches a list of PrintCard records matching the given arte_id (codigo_arte)."""
    if not arte_id:
        frappe.throw("Parameter 'arte_id' is required")

    results = frappe.db.get_list(
        "PrintCard",
        filters={"codigo_arte": arte_id},
        fields=["name", "estado", "version_arte_interna", "version"]
    )

    # Concatenate 'version_arte_interna' and 'version' using a dot (.)
    for record in results:
        record["version_combined"] = f"{record['version_arte_interna']}.{record['version']}"

    # sort records by 'version_combined' in descending order
    results = sorted(results, key=lambda x: x["version_combined"], reverse=True)
    
    return results
