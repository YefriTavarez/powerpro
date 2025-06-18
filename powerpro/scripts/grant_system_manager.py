# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe

def create_system_manager_permissions():
    """
    Create Custom DocPerm for all non-child doctypes giving System Manager full access
    """
    # Get all doctypes that are not child tables
    doctypes = frappe.get_all(
        "DocType",
        filters={"istable": 0},
        fields=["name", "is_submittable"]
    )
    
    created_count = 0
    created_docperm_ids = []  # Array to store IDs of created Custom DocPerm records
    
    for doctype_info in doctypes:
        doctype_name = doctype_info.name
        is_submittable = doctype_info.is_submittable
        
        # Check if Custom DocPerm already exists for this doctype and role
        existing_perm = frappe.get_all(
            "Custom DocPerm",
            filters={
                "parent": doctype_name,
                "role": "System Manager"
            },
            limit=1
        )
        
        # Skip if permission already exists
        if existing_perm:
            print(f"Permission already exists for {doctype_name}")
            continue
        
        try:
            # Create Custom DocPerm document
            custom_docperm = frappe.get_doc({
                "doctype": "Custom DocPerm",
                "parent": doctype_name,
                "parenttype": "DocType",
                "parentfield": "permissions",
                "role": "System Manager",
                "read": 1,
                "write": 1,
                "create": 1,
                "delete": 1,
                "share": 1,
                "report": 1,
                "export": 1,
                "import": 1,
                "set_user_permissions": 1,
                # Set submit, cancel, amend only if doctype is submittable
                "submit": 1 if is_submittable else 0,
                "cancel": 1 if is_submittable else 0,
                "amend": 1 if is_submittable else 0
            })
            
            custom_docperm.insert()
            created_docperm_ids.append(custom_docperm.name)  # Store the ID
            created_count += 1
            print(f"Created permission for {doctype_name} (ID: {custom_docperm.name}, Submittable: {bool(is_submittable)})")
            
        except Exception as e:
            print(f"Error creating permission for {doctype_name}: {str(e)}")
    
    # Commit the changes
    frappe.db.commit()
    
    print(f"\nCompleted! Created {created_count} Custom DocPerm entries.")
    print(f"Created Custom DocPerm IDs: {created_docperm_ids}")
    
    return created_docperm_ids

# Run the function
if __name__ == "__main__":
    site = "igcaribe.erpnext.com"
    sites_path = "/home/frappe/frappe-bench/sites"

    import os
    os.chdir(sites_path)

    print(os.getcwd())

    frappe.init(site=site, sites_path=sites_path)
    frappe.connect(site=site)

    docperm_ids = create_system_manager_permissions()

    print(f"\nTotal IDs created: {len(docperm_ids)}")
    with open("../created_docperm_ids.txt", "w") as f:
        f.write("\n".join(docperm_ids))
        print(f"Created DocPerm IDs saved to created_docperm_ids.txt")

    frappe.destroy()
    print("Database connection closed.")