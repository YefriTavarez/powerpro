import frappe
from frappe import _
from frappe.utils import flt

def run_reposting_tool(doc):
    try:
        # Resolve items based on document configuration
        items = resolve_items(doc)

        if not items:
            frappe.msgprint(_("No items found to process."), alert=True)
            return

        frappe.msgprint(_("Found {0} items to process.").format(len(items)), alert=True)

        # Process each item
        processed_count = 0
        for item in items:
            try:
                process_item(doc, item['item_code'], doc.available_qty, doc.dry_run)
                processed_count += 1
            except Exception as item_error:
                traceback = frappe.get_traceback(with_context=True)
                frappe.log_error(
                    title=f"Error processing item {item['item_code']}: {str(item_error)}", 
                    message=traceback,
                )
                continue

        # # Final status message
        # if doc.dry_run:
        #     frappe.msgprint(
        #         _("Dry run completed. {0} items would be processed.").format(processed_count),
        #         alert=True,
        #         indicator="blue"
        #     )
        # else:
        #     frappe.msgprint(
        #         _("Processing completed. {0} items successfully processed.").format(processed_count),
        #         alert=True,
        #         indicator="green"
        #     )

    except Exception as e:
        frappe.log_error(
            message=f"Run Reposting Tool Error: {str(e)}", 
            title="Stock Item Reposting Tool Error"
        )
        frappe.msgprint(
            _("Error during reposting: {0}").format(str(e)), 
            alert=True,
            indicator="red"
        )
        raise

def resolve_items(doc):
    try:
        items = []

        if doc.mode == 'Individual':
            if doc.item:
                if frappe.db.exists("Item", doc.item):
                    items.append({'item_code': doc.item})
                else:
                    frappe.throw(_("Item {0} does not exist").format(doc.item))
            else:
                frappe.throw(_("Please select an item for individual mode"))
                
        elif doc.mode == 'Batch':
            if doc.item_group:
                group_items = get_items_from_group(doc.item_group)
                items.extend(group_items)
            
            if doc.item_list_paste:
                pasted_items = []
                for line in doc.item_list_paste.splitlines():
                    item_code = line.strip()
                    if item_code and frappe.db.exists("Item", item_code):
                        pasted_items.append({'item_code': item_code})
                    else:
                        frappe.msgprint(
                            _("Item {0} does not exist and will be skipped").format(item_code),
                            alert=True,
                            indicator="orange"
                        )
                items.extend(pasted_items)

        seen = set()
        unique_items = []
        for item in items:
            if item['item_code'] not in seen:
                seen.add(item['item_code'])
                unique_items.append(item)

        return unique_items

    except Exception as e:
        frappe.log_error(
            message=f"Resolve Items Error: {str(e)}", 
            title="Stock Item Reposting Tool - Resolve Items Error"
        )
        raise

def get_items_from_group(group):
    try:
        items = []

        if not group:
            return items

        if not frappe.db.exists("Item Group", group):
            frappe.throw(_("Item Group {0} does not exist").format(group))

        direct_items = frappe.db.sql(
            """
            SELECT name as item_code
            FROM `tabItem`
            WHERE item_group = %s
            AND disabled = 0
            """, (group,), as_dict=True)

        items.extend(direct_items)

        child_groups = frappe.db.sql(
            """
            SELECT name
            FROM `tabItem Group`
            WHERE parent_item_group = %s
            AND is_group = 1
            """, (group,), as_dict=True)

        for child_group in child_groups:
            child_items = get_items_from_group(child_group.name)
            items.extend(child_items)

        return items

    except Exception as e:
        frappe.log_error(
            message=f"Get Items From Group Error for group {group}: {str(e)}", 
            title="Stock Item Reposting Tool - Get Items From Group Error"
        )
        raise

def process_item(doc, item_code, available_qty, dry_run):
    try:
        if not item_code:
            return

        item_doc = frappe.get_doc("Item", item_code)

        # Dynamic determination of stock status
        should_be_stock_item = True # available_qty > 0

        if dry_run:
            frappe.msgprint(
                _("DRY RUN - Item {0}: Would change is_stock_item from {1} to {2}").format(
                    item_code, 
                    item_doc.is_stock_item, 
                    should_be_stock_item
                ),
                alert=True,
                indicator="blue"
            )
            return

        # if item_doc.is_stock_item == should_be_stock_item:
        #     frappe.msgprint(
        #         _("Item {0}: No change needed (already {1})").format(
        #             item_code, 
        #             "stock item" if should_be_stock_item else "non-stock item"
        #         ),
        #         alert=True,
        #         indicator="gray"
        #     )
        #     return

        cancelled_pks = cancel_stock_transactions(item_code)

        item_doc.is_stock_item = should_be_stock_item
        item_doc.modified_by = frappe.session.user
        item_doc.modified = frappe.utils.now()
        item_doc.db_update()

        item_doc.notify_update()

        item_doc.add_comment("Comment", _("Stock item reposting tool: Item {0} updated to {1}").format(item_code, "stock item" if should_be_stock_item else "non-stock item")) 
        frappe.db.commit()

        frappe.msgprint(
            _("Item {0}: Successfully updated to {1}").format(
                item_code, 
                "stock item" if should_be_stock_item else "non-stock item"
            ),
            alert=True,
            indicator="green"
        )

        resubmit_stock_transactions(item_code,cancelled_pks)

        doc.add_comment("Comment", get_comment_text(item_code, cancelled_pks, should_be_stock_item))

    except Exception as e:
        frappe.log_error(
            message=f"Process Item Error for item {item_code}: {str(e)}", 
            title="Stock Item Reposting Tool - Process Item Error"
        )
        frappe.msgprint(
            _("Error processing item {0}: {1}").format(item_code, str(e)), 
            alert=True,
            indicator="red"
        )
        raise

def get_comment_text(item_code, cancelled_pks, should_be_stock_item) -> str:
    comment = _("Stock item reposting tool: Item {0} updated to {1}").format(item_code, "stock item" if should_be_stock_item else "non-stock item")
    for pk in cancelled_pks:
        comment += "\nCancelled {0} stock transactions for item {1}".format(pk[0], pk[1])
    return comment



def cancel_stock_transactions(item_code) -> list[str]:
    cancelled_pks = []
    try:
        for doctype in [
            "Delivery Note",
            "Purchase Receipt",
            "Stock Entry",
            "Sales Invoice",
            "Purchase Invoice",
            "Stock Reconciliation",
        ]:
            childtype = f"{doctype} Item"
            if doctype == "Stock Entry":
                childtype = "Stock Entry Detail"

            stock_entries = frappe.get_all(
                childtype,
                filters={
                    "item_code": item_code,
                    "docstatus": 1,
                },
                fields=["parent", "docstatus"],
                order_by="creation desc",
            )
            for entry in stock_entries:
                doc = frappe.get_doc(doctype, entry.parent)
                doc.docstatus = 2
                doc.set_docstatus()

                doc.on_cancel()

                cancelled_pks.append((doctype, doc.name))

        if cancelled_pks:
            frappe.msgprint(
                _("Cancelled {0} stock transactions for item {1}").format(len(cancelled_pks), item_code),
                alert=True,
                indicator="orange"
            )
        return cancelled_pks
    except Exception as e:
        frappe.log_error(
            message=f"Cancel Stock Transactions Error for item {item_code}: {str(e)}", 
            title="Cancel Stock Transactions Error"
        )
        raise

def resubmit_stock_transactions(item_code, cancelled_pks) -> list[str]:
    resubmitted_pks = []
    try:
        for pk in cancelled_pks:
            doc = frappe.get_doc(pk[0], pk[1])
            doc.docstatus = 1
            doc.set_docstatus()
            doc.on_submit()
            resubmitted_pks.append(doc.name)

            doc.add_comment("Comment", _("Stock item reposting tool: Stock transaction {0} resubmitted for item {1}").format(doc.name, item_code))

        if resubmitted_pks:
            frappe.msgprint(
                _("Resubmitted {0} stock transactions").format(len(resubmitted_pks)),
                alert=True,
                indicator="green"
            )
        return resubmitted_pks
    except Exception as e:
        frappe.log_error(
            message=f"Resubmit Stock Transactions Error: {str(e)}", 
            title="Resubmit Stock Transactions Error"
        )
        raise
