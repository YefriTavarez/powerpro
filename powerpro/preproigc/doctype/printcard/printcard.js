// Copyright (c) 2025, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on("PrintCard", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}

		const can_generate_pdf =
			frappe.session.user === "Administrator" ||
			frappe.user.has_role(["System Manager"]);

		if (!can_generate_pdf) {
			return;
		}

		frm.add_custom_button(__("Generar PDF PrintCard"), () => {
			frm.call("generate_printcard_pdf_on_demand")
				.then((response) => {
					const message = response?.message?.message;

					if (message) {
						frappe.show_alert({
							message,
							indicator: "green",
						});
					}

					frm.reload_doc();
				});
		}, __("Actions"));
	},
});
