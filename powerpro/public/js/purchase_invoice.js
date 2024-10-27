frappe.ui.form.on("Purchase Invoice", {
	refresh(frm){
		frappe.run_serially([
			_ => frm.trigger("set_queries"),
		]);

		frm.set_query("ibtis_retention_type", () => {
			return {
				"filters": {
					"isr": 0
				}
			}
		})
		
		frm.set_query("isr_type", () => {
			return {
				"filters": {
					"isr": 1
				}
			}
		})
	},
	validate(frm){
		frm.trigger("ncf");
		frm.trigger("validate_cost_center");
		// frm.trigger("validate_ncf")
		
	},
	before_save(frm) {
		frm.trigger("validate_ncf");
		frm.trigger("update_taxes_amount")
		if (frappe.validated === false) {
            // Asegúrate de que no continúe si no ha sido validado correctamente
            frappe.validated = false;
            return false;  // Este return previene la ejecución de guardado
        }
	},

	ncf(frm){
		let {ncf} = frm.doc;

		frm.set_df_property("vencimiento_ncf", "reqd", !!ncf);
		
		if (!ncf)
			return
		
		frm.set_value("ncf", ncf.trim().toUpperCase())
	},

	validate_rnc(frm){
		let len = frm.doc.tax_id.length;

		if (![9, 11].includes(len)) {
			frappe.msgprint(`El RNC/Cedula ingresados tiene <b>${len}</b> caracteres favor verificar, deben ser 9 u 11.`);
			frappe.validated = false;
			return
		}
	},
	validate_cost_center(frm){
		if(!frm.doc.cost_center)
			return
		$.map(frm.doc.taxes, tax => {
			if (!tax.cost_center)
				tax.cost_center = frm.doc.cost_center;
		})
		$.map(frm.doc.items, tax => {
			if (!tax.cost_center)
				tax.cost_center = frm.doc.cost_center;
		})

	},
	tax_id(frm){
		if (!frm.doc.tax_id)
			return
		frm.set_value("tax_id", replace_all(frm.doc.tax_id.trim(), "-", ""));
		frm.trigger("validate_rnc");
	},

	set_queries(frm) {
		frappe.run_serially([
			() => frm.trigger("set_retention_query"),
			() => frm.trigger("set_isr_rate_query"),
			() => frm.trigger("set_details_of_service_purchased_query"),
		]);
	},
	set_retention_query(frm) {
		const { doc } = frm;

		const fieldname = "retention";

		const get_query = function () {
			const filters = {
				"retention_type": ["!=", "ISR"],
				"applicable_for": "Pay",
			};
			return { filters };
		};

		frm.set_query(fieldname, get_query);
	},
	set_isr_rate_query(frm) {
		const { doc } = frm;

		const fieldname = "isr_rate";

		const get_query = function () {
			const filters = {
				"retention_type": "ISR",
			};
			return { filters };
		};

		frm.set_query(fieldname, get_query);
	},
	set_details_of_service_purchased_query(frm) {
		const { doc } = frm;
		const fieldname = "details_of_service_purchased";
		const get_query = function () {
			const filters = {
				"service_purchased": doc.type_of_service_purchased || "",
			};
			return { filters };
		}

		frm.set_query(fieldname, get_query);
	},
	retention(frm) {
		// frappe.msgprint("retention");
		// if (!frm.doc.retention) {
		// 	return "Skip for empty retention";
		// }

		frm.call({
			method: "powerpro.controllers.purchase_invoice.get_retention_details",
			args: {
				base_total_taxes_and_charges: frm.doc.base_total_taxes_and_charges,
				total: frm.doc.total,
				retention_type: frm.doc.retention,
			},
		}).then(({ message }) => {
			const { amount } = message;

			frm.set_value("retention_amount", amount);
		});
	},

	isr_rate(frm) {
		if (!frm.doc.isr_rate) {
			return "Skip for empty isr_rate";
		}

		frm.call({
			method: "powerpro.controllers.purchase_invoice.get_retention_details",
			args: {
				base_total_taxes_and_charges: frm.doc.base_total_taxes_and_charges,
				total: frm.doc.total,
				retention_type: frm.doc.isr_rate,
			},
		}).then(({ message }) => {
			const { amount } = message;

			frm.set_value("isr_amount", amount);
		});
	},
	
});

