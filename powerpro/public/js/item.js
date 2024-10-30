// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

{
	function refresh(frm) {
		_toggle_disable_form(frm);
		_set_item_group_filters(frm);
	}

	function _toggle_disable_form(frm) {
		const { doc } = frm;
		
		if (
			doc.reference_type
			&& doc.reference_name
		) {
			frm.disable_form();
			frm.set_intro(
				__("This Item is linked to a {0} record, you can't edit it here.", [doc.reference_type]), "red"
			)
		}
	}

	function _set_item_group_filters(frm) {
		_set_item_group_2_filter(frm);
		_set_item_group_3_filter(frm);
		_set_item_group_4_filter(frm);
		_set_item_group_5_filter(frm);
	}

	function _set_item_group_2_filter(frm) {
		frm.set_query("custom_item_group_2", function() {
			return {
				"filters": {
					"parent_item_group": frm.doc.custom_item_group_1,
				},
			};
		});
	}

	function _set_item_group_3_filter(frm) {
		frm.set_query("custom_item_group_3", function() {
			return {
				"filters": {
					"parent_item_group": frm.doc.custom_item_group_2,
				},
			};
		});
	}

	function _set_item_group_4_filter(frm) {
		frm.set_query("custom_item_group_4", function() {
			return {
				"filters": {
					"parent_item_group": frm.doc.custom_item_group_3,
				},
			};
		});
	}

	function _set_item_group_5_filter(frm) {
		frm.set_query("custom_item_group_5", function() {
			return {
				"filters": {
					"parent_item_group": frm.doc.custom_item_group_4,
				},
			};
		});
	}

	function custom_item_group_1(frm) {
		if (frm.doc.custom_item_group_1) {
			frm.set_value("item_group", frm.doc.custom_item_group_1);

			setTimeout(() => {
				frm.get_field("custom_item_group_2").$input.focus();
			}, 500);
		} else {
			frm.set_value("item_group", null)
		}

		frm.set_value("custom_item_group_2", null);
		frm.set_value("custom_item_group_3", null);
		frm.set_value("custom_item_group_4", null);
		frm.set_value("custom_item_group_5", null);
	}

	function custom_item_group_2(frm) {
		if (frm.doc.custom_item_group_2) {
			frm.set_value("item_group", frm.doc.custom_item_group_2);

			setTimeout(() => {
				frm.get_field("custom_item_group_3").$input.focus();
			}, 500);
		} else {
			frm.set_value("item_group", frm.doc.custom_item_group_1)
		}

		frm.set_value("custom_item_group_3", null);
		frm.set_value("custom_item_group_4", null);
		frm.set_value("custom_item_group_5", null);
	}

	function custom_item_group_3(frm) {
		if (frm.doc.custom_item_group_3) {
			frm.set_value("item_group", frm.doc.custom_item_group_3);

			setTimeout(() => {
				frm.get_field("custom_item_group_4").$input.focus();
			}, 500);
		} else {
			frm.set_value("item_group", frm.doc.custom_item_group_2)
		}

		frm.set_value("custom_item_group_4", null);
		frm.set_value("custom_item_group_5", null);
	}

	function custom_item_group_4(frm) {
		if (frm.doc.custom_item_group_4) {
			frm.set_value("item_group", frm.doc.custom_item_group_4);

			setTimeout(() => {
				frm.get_field("custom_item_group_5").$input.focus();
			}, 500);
		} else {
			frm.set_value("item_group", frm.doc.custom_item_group_3)
		}

		frm.set_value("custom_item_group_5", null);
	}

	function custom_item_group_5(frm) {
		if (frm.doc.custom_item_group_5) {
			frm.set_value("item_group", frm.doc.custom_item_group_5);
		} else {
			frm.set_value("item_group", frm.doc.custom_item_group_4)
		}
	}

	frappe.ui.form.on("Item", {
		refresh,
		custom_item_group_1,
		custom_item_group_2,
		custom_item_group_3,
		custom_item_group_4,
		custom_item_group_5,
	});
}