// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt

{
	// std events
	function setup(frm) {
		const method = "get_item_group_root";
		const args = {
			// empty
		};
		function callback({ message: root_item_group }) {
			frm.root_item_group = root_item_group;
		}

		frm.call(method, args, callback);
	}

	function refresh(frm) {
		_set_queries(frm);
	}

	// private methods
	function _set_queries(frm) {
		frm.set_query("item_group_1", function() {
			return {
				"filters": {
					"parent_item_group": frm.root_item_group,
				},
			};
		});

		frm.set_query("item_group_2", function() {
			return {
				"filters": {
					"parent_item_group": frm.doc.item_group_1,
				},
			};
		});

		frm.set_query("item_group_3", function() {
			return {
				"filters": {
					"parent_item_group": frm.doc.item_group_2,
				},
			};
		});

		frm.set_query("item_group_4", function() {
			return {
				"filters": {
					"parent_item_group": frm.doc.item_group_3,
				},
			};
		});

		frm.set_query("item_group_5", function() {
			return {
				"filters": {
					"parent_item_group": frm.doc.item_group_4,
				},
			};
		});
	}

	// field handlers
	function item_group_1(frm) {
		frm.set_value("item_group_2", "");
		frm.set_value("is_group_2", "");
	}

	function item_group_2(frm) {
		frm.set_value("item_group_3", "");
		frm.set_value("is_group_3", "");
	}

	function item_group_3(frm) {
		frm.set_value("item_group_4", "");
		frm.set_value("is_group_4", "");
	}

	function item_group_4(frm) {
		frm.set_value("item_group_5", "");
		frm.set_value("is_group_5", "");
	}

	function item_group_5(frm) {
		// nothing to do
	}

	frappe.ui.form.on("Product Type", {
		setup,
		refresh,
		item_group_1,
		item_group_2,
		item_group_3,
		item_group_4,
		item_group_5,
	});
}