"""Transactional, date-scoped numbering for payroll bank batches.

Only Frappe's internal Series counter is written here. The caller's document
save owns the transaction, so a failed save also rolls back its reservation.
"""

import frappe
from frappe import _
from frappe.utils import getdate


SERIES_PREFIX = "POWERPRO-BANK-PAYMENT-"
MAX_SEQUENCE = 9_999_999


def reserve_payment_sequence(payment_date):
    if not payment_date:
        frappe.throw(_("Payment Date is required before assigning a payment sequence."))
    payment_date = getdate(payment_date)
    key = f"{SERIES_PREFIX}{payment_date.isoformat()}"

    # An upsert locks even the first reservation for a date. Selecting a missing
    # row and then inserting it would allow concurrent first-save races.
    frappe.db.multisql(
        {
            "mariadb": """INSERT INTO `tabSeries` (`name`, `current`) VALUES (%s, 0)
                ON DUPLICATE KEY UPDATE `name` = `name`""",
            "postgres": """INSERT INTO "tabSeries" ("name", "current") VALUES (%s, 0)
                ON CONFLICT ("name") DO NOTHING""",
        },
        (key,),
    )
    current = frappe.db.sql(
        "SELECT `current` FROM `tabSeries` WHERE `name` = %s FOR UPDATE", (key,)
    )[0][0] or 0

    # Include legacy/manual sequences and cancelled batches, across all bank
    # profiles. Never reuse a committed reservation after deletion/cancellation.
    existing = frappe.db.sql(
        "SELECT payment_sequence FROM `tabPayroll Bank Batch` WHERE payment_date = %s",
        (payment_date,),
    )
    highest = max(
        (int(row[0]) for row in existing if row[0] and row[0].isascii() and row[0].isdigit()),
        default=0,
    )
    number = max(int(current), highest) + 1
    if number > MAX_SEQUENCE:
        frappe.throw(_("The seven-digit payment sequence is exhausted for {0}.").format(payment_date))
    frappe.db.sql(
        "UPDATE `tabSeries` SET `current` = %s WHERE `name` = %s", (number, key)
    )
    return f"{number:07d}"
