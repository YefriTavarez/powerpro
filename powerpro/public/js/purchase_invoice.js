{
	function _prompt_company(frm) {
		const fields = [
			{
				fieldname: "company",
				fieldtype: "Link",
				options: "Company",
				label: __("Company"),
				reqd: true,
			},
		];
	
		const title = __("Seleccione la compañía para continuar");
		const primary_label = __("Continue");
		function callback({ company }) {
			frappe.run_serially([
				async function() {
					const exists = await frappe.db.exists("Supplier", `${company}`);
					
					if (!exists) {
						frappe.throw(`El proveedor <b>${company}</b> no existe en el sistema, favor verificar.`);
					}
				},
				async function() {
					await frm.set_value("company", company);
				},
				async function() {
					await frm.set_value("supplier", company);
				},
			]);
			// frm.set_value("tax_id", frm.doc.company_tax_id);
		}
		
		frappe.prompt(fields, callback, title, primary_label);
	}

	function _validate_rnc(frm) {
		let len = frm.doc.tax_id.length;

		if (![9, 11].includes(len)) {
			frappe.msgprint(`El RNC/Cedula ingresados tiene <b>${len}</b> caracteres favor verificar, deben ser 9 u 11.`);
			frappe.validated = false;
			return false; 
		}
	}

	function _validate_cost_center(frm) {
		if (!frm.doc.cost_center) {
			return ; // no cost center is a valid cost center
		}

		jQuery.map(frm.doc.taxes, tax => {
			if (!tax.cost_center)
				tax.cost_center = frm.doc.cost_center;
		})

		jQuery.map(frm.doc.items, tax => {
			if (!tax.cost_center)
				tax.cost_center = frm.doc.cost_center;
		})
	}

	function _set_queries(frm) {
		const { doc } = frm;

		frappe.run_serially([
			function _set_retention_query() {
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
			function _set_isr_rate_query() {
				const fieldname = "isr_rate";
		
				const get_query = function () {
					const filters = {
						"retention_type": "ISR",
					};
					return { filters };
				};
		
				frm.set_query(fieldname, get_query);
			},
			function _set_details_of_service_purchased_query() {
				const fieldname = "details_of_service_purchased";
				const get_query = function () {
					const filters = {
						"service_purchased": doc.type_of_service_purchased || "",
					};
					return { filters };
				}
		
				frm.set_query(fieldname, get_query);
			},
			function _set_ibtis_retention_type_query() {
				frm.set_query("ibtis_retention_type", () => {
					return {
						"filters": {
							"isr": 0
						}
					}
				});
			},
			function _set_isr_type_query() {
				frm.set_query("isr_type", () => {
					return {
						"filters": {
							"isr": 1
						}
					}
				});
			},
		]);
	}


	frappe.ui.form.on("Purchase Invoice", {
		refresh(frm) {
			const { doc } = frm;
			_set_queries(frm);

			if (
				doc.docstatus === 0
			) {
				frm.add_custom_button(__("Gastos Menores"), () => {
					_prompt_company(frm);
				}, "Acciones");
			}
		},

		validate(frm) {
			_validate_rnc(frm);
			_validate_cost_center(frm);
		},

		before_save(frm) {
			frm.trigger("update_taxes_amount")
		},

		ncf(frm) {
			const { ncf } = frm.doc;

			frm.set_df_property("vencimiento_ncf", "reqd", Boolean(ncf));

			if (ncf) {
				frm.set_value("ncf", ncf.trim().toUpperCase())
			}
		},

		tax_id(frm) {
			const { tax_id } = frm.doc;

			if (tax_id) {
				frm.set_value("tax_id", replace_all(frm.doc.tax_id.trim(), "-", ""));
				_validate_rnc(frm);
			}
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
}