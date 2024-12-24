// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

{
	function refresh(frm) {
		frm.set_query("workstation", function() {
			return {
				query: "powerpro.controllers.queries.get_workstation",
				filters: {
					"operation_type": frm.doc.operation_type,
				},
			};
		});
		frm.set_query("available_workstations", function() {
			return {
				query: "powerpro.controllers.queries.get_workstation",
				filters: {
					"operation_type": frm.doc.operation_type,
				},
			};
		});
	}

	function workstation(frm) {
		const { doc } = frm;

		if (!doc.workstation) {
			return ; // only if workstation is set
		}

		// let's add the workstation to the available_workstations table,
		// but only if it's not already there
		const available_workstations = doc.available_workstations || [];
		const is_already_added = available_workstations.some(
			({ workstation }) => workstation === doc.workstation
		);

		if (!is_already_added) {
			frm.add_child("available_workstations", {
				workstation: doc.workstation,
			});

			frm.refresh_field("available_workstations");
		}
	}

	frappe.ui.form.on("Operation", {
		refresh,
		workstation,
	});
}