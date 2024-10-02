frappe.ui.form.on("Payment Entry", {
	refresh(frm) {
		frappe.run_serially([
			_ => frm.trigger("set_queries"),
		]);
	},
	set_queries(frm) {
		frappe.run_serially([
			_ => frm.trigger("set_retention_query"),
			_ => frm.trigger("set_isr_rate_query"),
		]);

	},
	set_retention_query(frm) {
		const { doc } = frm;

		const fieldname = "retention";
		const parentfield = "references";

		const get_query = function () {
			const supported_types = new Set([
				"Pay",
				"Receive",
			]);

			if (!supported_types.has(doc.payment_type)) {
				frappe.throw(`Payment Type '${doc.payment_type}' is not supported`);
			}

			const filters = {
				"applicable_for": doc.payment_type,
			};

			return { filters };
		};

		frm.set_query(fieldname, parentfield, get_query);
	},
	set_isr_rate_query(frm) {
		const { doc } = frm;

		const fieldname = "isr_rate";
		const parentfield = "references";

		const get_query = function () {
			const supported_types = new Set([
				"Pay",
				"Receive",
			]);

			if (!supported_types.has(doc.payment_type)) {
				frappe.throw(`Payment Type '${doc.payment_type}' is not supported`);
			}

			const filters = {
				"retention_type": "ISR",
			};

			return { filters };
		};

		frm.set_query(fieldname, parentfield, get_query);
	}
});

frappe.ui.form.on("Payment Entry Reference", {
	retention(frm, doctype, name) {
		const { deductions, references } = frm.doc;

		const doc = frappe.get_doc(doctype, name);

		if (!doc.retention) {
			return "Skip for empty retention";
		}

		frm.call("get_retention_details", {
			reference_doctype: doc.reference_doctype,
			reference_name: doc.reference_name,
			retention_id: doc.retention,
		}).then(({ message }) => {
			const {
				account,
				amount,
				cost_center,
				retention_description,
			} = message;

			frappe.model.set_value(doctype, name, "retention_amount", amount);

			const deductions = frm.doc.deductions;
			const deduction = {
				cost_center: cost_center,
				amount: amount,
				description: retention_description,
			};
			const exists = deductions.some(item =>
				item.cost_center === deduction.cost_center &&
				item.description === deduction.description
			);

			if (exists) {
				deductions.filter(item =>
					item.cost_center === deduction.cost_center &&
					item.description === deduction.description

				).map((item) => {
					const doc = frappe.get_doc(item.doctype, item.name)
					const index = deductions.indexOf(doc)
					deductions.splice(index, 1)
				})

				deductions.map((item, index) => {
					item.idx = index + 1
				})
			}
			frm.add_child("deductions", {
				"account": account,
				"cost_center": cost_center,
				"amount": -1 * amount,
				"description": retention_description,
			});
			frm.refresh_field("deductions");
		});
	},

	isr_rate(frm, doctype, name) {
		const { deductions, references } = frm.doc;

		const doc = frappe.get_doc(doctype, name);

		if (!doc.isr_rate) {
			return "Skip for empty isr_rate";
		}

		frm.call("get_retention_details", {
			reference_doctype: doc.reference_doctype,
			reference_name: doc.reference_name,
			retention_id: doc.isr_rate,
		}).then(({ message }) => {


			const {
				account,
				amount,
				cost_center,
				retention_description,
			} = message;

			frappe.model.set_value(doctype, name, "isr_amount", amount);

			const existing_deduction = deductions
				.find(deduction => deduction.account === account);


			if (existing_deduction) {
				// check to see if the is another row with the same retention_type
			}
			const deductions = frm.doc.deductions;
			const deduction = {
				cost_center: cost_center,
				amount: amount,
				description: retention_description,
			};
			const exists = deductions.some(item =>
				item.cost_center === deduction.cost_center &&
				item.description === deduction.description
			);
			if (exists) {
				deductions.filter(item =>
					item.cost_center === deduction.cost_center &&
					item.description === deduction.description

				).map((item) => {
					const doc = frappe.get_doc(item.doctype, item.name)
					const index = deductions.indexOf(doc)
					deductions.splice(index, 1)
				})

				deductions.map((item, index) => {
					item.idx = index + 1
				})
			}
			frm.add_child("deductions", {
				"account": account,
				"cost_center": cost_center,
				"amount": -1 * amount,
				"description": retention_description,
			});
			frm.refresh_field("deductions");
		});


	},
});