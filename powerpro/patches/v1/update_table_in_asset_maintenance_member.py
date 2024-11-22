import frappe


def execute():
    # Verify if the index in the team_member column exists
    index_exists = frappe.db.sql("""
        SELECT COUNT(1)
        FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'tabMaintenance Team Member'
          AND INDEX_NAME = 'team_member'
    """)[0][0]

    # if the index exists, drop it
    if index_exists:
        frappe.db.sql("""
            ALTER TABLE `tabMaintenance Team Member`
            DROP INDEX `team_member`;
        """)
        frappe.db.commit()
        print("Index team_member deleted.")
    else:
        print("Index team_member does not exist. Nothing to do.")