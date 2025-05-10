// Copyright (c) 2025, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

{
	const { onload: original } = erpnext.TransactionController.prototype;
	erpnext.TransactionController.prototype.onload = function() {
		// call the original onload function
		original.apply(this, arguments);

		const self = this;

		// this is the only change to the original code
		// add an onload handler to all the forms
		// that implement the TransactionController...
		// say, Sales Order, Purchase Order, Sales Invoice, etc.
		// this will be used to set the exchange rate
		// when the document is created from a previous document
		frappe.ui.form.on(this.frm.doctype, {
			onload_post_render(frm) {
				const { doc } = frm;
				const { __islocal: is_new, __onload: bootinfo } = doc;

				if (
					is_new
					&& bootinfo?.load_after_mapping
				) {
					// The transaction date be either transaction_date (from orders) or posting_date (from invoices)
					let transaction_date = doc.transaction_date || doc.posting_date;

					let company_currency = self.get_company_currency();
					// Added `load_after_mapping` to determine if document is loading after mapping from another doc
					if(
						doc.currency && doc.currency !== company_currency
						&& doc.__onload?.load_after_mapping
					) {
						self.get_exchange_rate(transaction_date, doc.currency, company_currency,
						function(exchange_rate) {
							if(exchange_rate != doc.conversion_rate) {
								self.set_margin_amount_based_on_currency(exchange_rate);
								self.set_actual_charges_based_on_currency(exchange_rate);
								self.frm.set_value("conversion_rate", exchange_rate);
							}
						});
					}
				}
			},
		});
	};
}