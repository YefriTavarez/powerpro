// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

{
	const { has_indicator: original } = frappe;

	frappe.has_indicator = function(doctype) {
		const skip_list = [
			"Raw Material",
		];
		
		if (
			skip_list.includes(doctype)
		) {
			return false;
		}

		const always_list = [
			"PrintCard",
		];

		if (
			always_list.includes(doctype)
		) {
			return true;
		}
		
		return original(doctype);
	};
}