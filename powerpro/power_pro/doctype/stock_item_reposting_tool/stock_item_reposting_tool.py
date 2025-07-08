# Copyright (c) 2025, Yefri Tavarez and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class StockItemRepostingTool(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        available_qty: DF.Float
        dry_run: DF.Check
        item: DF.Link | None
        item_group: DF.Link | None
        item_list_paste: DF.Text | None
        mode: DF.Literal["Individual", "Batch"]
    # end: auto-generated types

    @frappe.whitelist()
    def execute_tool(self):
        """Execute the stock item reposting tool"""
        try:
            # Call the reposting tool method
            self.run_reposting_tool()
            
            # Provide success feedback to the user
            frappe.msgprint("Stock item reposting tool executed successfully!", alert=True)
            
        except Exception as e:
            # Provide error feedback to the user
            frappe.msgprint(f"Error executing reposting tool: {str(e)}", alert=True)
            frappe.log_error(f"Stock Item Reposting Tool Error: {str(e)}")
            raise

    def run_reposting_tool(self):
        """Main logic for running the reposting tool"""
        from .utils import run_reposting_tool
        run_reposting_tool(self)
        

@frappe.whitelist()
def execute_reposting_tool(doc_name):
    """Whitelisted method to execute the reposting tool from frontend"""
    doc = frappe.get_doc("Stock Item Reposting Tool", doc_name)
    doc.execute_tool()
    return {"status": "success", "message": "Reposting tool executed successfully"}
