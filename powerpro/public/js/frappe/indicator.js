// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

{
	const { has_indicator: original } = frappe;

	frappe.has_indicator = function(doctype) {
		const skip_list = [
			"Raw Material",
			"PrintCard",
		];

		if (
			skip_list.includes(doctype)
		) {
			return false;
		}
		
		return original(doctype);
	};
}