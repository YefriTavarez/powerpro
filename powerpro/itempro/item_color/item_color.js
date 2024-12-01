// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt

{
	function onload(frm) {
		_set_queries(frm);
	}

	function _set_queries(frm) {
		frm.set_query("item_name", "item_names", function(parent, doctype, name) {
			const doc = frappe.get_doc(doctype, name);
			const ignore_list = parent
				.item_names
				.filter(d => d.item_name && d.item_name !== doc.item_name)
				.map(d => d.item_name)
			;

			
			const filters = {
				"name": ["Not In", ignore_list],
			};

			return { filters };
		});
	}

	frappe.ui.form.on(cur_frm.doctype, {
		onload,
	});
}