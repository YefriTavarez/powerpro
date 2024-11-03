// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt

{
	/*
	Tasks:

	- [ ] Validate sum of all percentages is 100 (before_save)
	- [ ] Ensure each Pantone Color is unique in the child table
	*/

	function refresh(frm) {
		_set_queries(frm);
	}

	function validate(frm) {
		_validate_uniqueness_of_formula(frm);
		_validate_sum_of_percentages(frm);
	}

	function _set_queries(frm) {
		_set_ink_color_queries(frm);
	}

	function _set_ink_color_queries(frm) {
		const fieldname = "ink_color";
		const parentfield = "pantone_composition";
		function get_query(doc, doctype, name) {
			// ignore all the values already selected in other rows of the child table
			const ignore_list = doc[parentfield]
				.filter(row => row.name !== name)
				.filter(row => Boolean(row.ink_color))
				.map(row => row.ink_color);


			if (!frm.is_new()) {
				ignore_list.push(frm.doc.name);
			}

			if (!ignore_list.length) {
				ignore_list.push("N/A");
			}

			const filters = {
				ink_type: "Pantone",
				pantone_type: "Base",
				name: ["not in", ignore_list],
			};

			return { filters };
		}

		frm.set_query(fieldname, parentfield, get_query);
	}

	function _validate_uniqueness_of_formula(frm) {
		const { doc } = frm;

		if (
			doc.ink_type !== "Pantone"
			|| doc.pantone_type !== "Formula"
		) {
			return ; // skip validation non-Pantone Formula based colors
		}

		// validates that each Pantone Color is unique in the child table
		const { pantone_composition } = doc;

		const duplicates = pantone_composition
			.map(row => row.ink_color)
			.filter((value, index, self) => self.indexOf(value) !== index);

		for (const ink_color of duplicates) {
			frappe.msgprint(__(`This Pantone Color ${ink_color} is already in the list!`));
		}
	}

	function _validate_sum_of_percentages(frm) {
		const { doc } = frm;

		if (
			doc.ink_type !== "Pantone"
			|| doc.pantone_type !== "Formula"
		) {
			return ; // skip validation non-Pantone Formula based colors
		}

		// validates that the sum of all percentages is 100
		const { pantone_composition } = doc;

		const sum = pantone_composition
			.map(row => row.percentage)
			.reduce((acc, cur) => acc + cur, 0);

		if (sum !== 100) {
			frappe.throw(__("The sum of all percentages must be 100!"));
		}
	}

	frappe.ui.form.on("Ink Color", {
		refresh,
		validate,
	});

	frappe.ui.form.on("Pantone Composition", {
		ink_color(frm, doctype, name) {
			const doc = frappe.get_doc(doctype, name);

			if (!doc.ink_color) {
				return;
			}

			frm.doc.pantone_composition
				.filter(row => row.name !== name)
				.filter(row => row.ink_color === doc.ink_color)
				.forEach(row => {
					frappe.show_alert({
						message: __(`This Pantone Color ${row.ink_color} is already in the list!`),
						indicator: "red",
					});

					// doc.ink_color = null;

					frappe
						.model
						.set_value(doctype, name, "ink_color", "");
				});
		},
	});


	// AVAILABLE FIELDS:
	//
	// ink_name: String
	// ink_type: Literal["Pantone", "Process"]
	// pantone_type: Literal["Base", "Formula", "Metallic"]
	// hexadecimal_color: String
	// rate_per_kg: Float
	// currency: String
	// pantone_composition: List[Dict]
}