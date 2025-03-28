# Copyright (c) 2025, Yefri Tavarez and Contributors
# For license information, please see license.txt

from typing import Union

import frappe
from frappe import _
from frappe.utils import flt

from erpnext.accounts.doctype.opening_invoice_creation_tool import (
	opening_invoice_creation_tool as erpnext
)

class OpeningInvoiceCreationTool(erpnext.OpeningInvoiceCreationTool):
	# overrides
	def get_invoice_dict(self, row=None):
		def get_item_dict():
			cost_center = row.get("cost_center") or frappe.get_cached_value(
				"Company", self.company, "cost_center"
			)
			if not cost_center:
				frappe.throw(
					_("Please set the Default Cost Center in {0} company.").format(frappe.bold(self.company))
				)

			income_expense_account_field = (
				"income_account" if row.party_type == "Customer" else "expense_account"
			)
			default_uom = frappe.db.get_single_value("Stock Settings", "stock_uom") or _("Nos")
			rate = flt(row.outstanding_amount) / flt(row.qty)

			item_dict = frappe._dict(
				{
					"uom": default_uom,
					"rate": rate or 0.0,
					"qty": row.qty,
					"conversion_factor": 1.0,
					"item_name": row.item_name or "Opening Invoice Item",
					"description": row.item_name or "Opening Invoice Item",
					income_expense_account_field: row.temporary_opening_account,
					"cost_center": cost_center,
				}
			)

			for dimension in erpnext.get_accounting_dimensions():
				item_dict.update({dimension: row.get(dimension)})

			return item_dict

		item = get_item_dict()

		invoice = frappe._dict(
			{
				"items": [item],
				"is_opening": "Yes",
				"set_posting_time": 1,
				"company": self.company,
				"cost_center": self.cost_center,
				"due_date": row.due_date,
				"posting_date": row.posting_date,
				frappe.scrub(row.party_type): row.party,
				"is_pos": 0,
				"doctype": "Sales Invoice" if self.invoice_type == "Sales" else "Purchase Invoice",
				"update_stock": 0,  # important: https://github.com/frappe/erpnext/pull/23559
				"invoice_number": row.invoice_number,
				"ncf": row.ncf,
				"disable_rounded_total": 1,
			}
		)

		accounting_dimension = erpnext.get_accounting_dimensions()
		for dimension in accounting_dimension:
			invoice.update({dimension: self.get(dimension) or item.get(dimension)})

		return invoice
	