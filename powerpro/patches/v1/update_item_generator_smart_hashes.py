# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe
import click


def execute():
    doctype = "Item Generator"
    click.echo(click.style(f"Starting update of smart hashes for {doctype} documents...", fg="blue"))

    item_names = frappe.get_all(doctype, pluck="name")

    if not item_names:
        click.echo(click.style(f"No documents found for {doctype}. Nothing to process.", fg="yellow"))
        return

    click.echo(f"Found {len(item_names)} {doctype} document(s) to process.")

    for name in item_names:
        click.echo(f"\nProcessing {doctype}: {name}...")
        doc = frappe.get_doc(doctype, name)

        previous_hash = doc.smart_hash
        click.echo(f"  Previous smart hash: {previous_hash}")

        doc.self_generate_smart_hash()  # This updates doc.smart_hash

        # doc.smart_hash now holds the potentially new hash
        click.echo(f"  Newly generated smart hash: {doc.smart_hash}")

        if doc.smart_hash != previous_hash:
            click.echo(click.style("  Smart hash changed. Updating document in the database.", fg="green"))
            doc.db_update()
        else:
            click.echo(click.style("  Smart hash remains the same. No database update required for hash change.", fg="cyan"))

        new_hash = doc.smart_hash  # Consistent with original code's new_hash variable

        comment_text = f"Smart Hash updated from {previous_hash} to {new_hash} on {frappe.utils.now()}."
        doc.add_comment(
            "Comment", comment_text,
        )
        click.echo(f"  Comment added to {doctype} '{name}'.")

    click.echo(click.style(f"\nFinished updating smart hashes for all processed {doctype} documents.", fg="blue"))
