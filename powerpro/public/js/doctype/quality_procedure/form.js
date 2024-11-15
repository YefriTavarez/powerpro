// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

{
	function override_save_action(frm) {
		const label = __("Save");
		function click(event) {
			const fields = [
				{
					fieldtype: "Select",
					label: __("Type of Update"),
					fieldname: "type_of_update",
					reqd: 1,
					options: [
						{label: __("Major Changes"), value: "bump_major"},
						{label: __("Minor Changes"), value: "bump_minor"},
						{label: __("Only Corrections"), value: "bump_patch"},
						{label: __("Styling / Format"), value: "save_only"},
					],
				},
			];
			function callback({ type_of_update: method }) {
				const args = {
					autosave: true,
				};

				frm.call(method, args)
					.then(response => {
						const { message } = response;

						if (!message) {
							frm.refresh();
							return;
						}

						if (message.startsWith("PRO-CAL-")) {
							// let's redirect the browser to the new document
							const doctype = "Quality Procedure";
							const docname = message;
							const route = `Form/${doctype}/${docname}`;
							frappe.set_route(route);
						}
					});
			};
			
			const title = __("Type of Changes");
			const primary_label = __("Save");

			if (frm.is_new()) {
				frm.save();
				return ; // we don't need to prompt the user
			}

			frappe.prompt(fields, callback, title, primary_label);
		}
		
		const icon = null;
		const working_label = `${__("Wait")}...`;
		frm.page.set_primary_action(label, click, icon, working_label);
	}

	function setup(frm) {
		frm.$wrapper.on("dirty", function(event) {
			override_save_action(frm);
		});
	}

	frappe.ui.form.on("Quality Procedure", {
		setup,
	});
}
