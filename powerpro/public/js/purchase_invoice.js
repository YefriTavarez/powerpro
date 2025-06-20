{
	function _prompt_company(frm) {
		const { doc } = frm;
		
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
					if (doc.supplier) {
						await frm.set_value("supplier", "");
					}
				},
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

	function _prompt_for_minor_expesenses_details(frm) {
		const { doc } = frm;

		frappe.prompt([
			{
				label: 'Compañía',
				fieldname: 'company',
				fieldtype: 'Link',
				options: 'Company',
				read_only: 1,
				default: doc.company,
			},
			{
				fieldtype: "Section Break",
			},
			{
				label: 'Fecha de Referencia',
				fieldname: 'reference_date',
				fieldtype: 'Date',
				reqd: 1
			},
			{
				label: 'No. de Referencia',
				fieldname: 'reference_number',
				fieldtype: 'Data',
				reqd: 0
			},
			{
				fieldtype: "Column Break",
			},
			{
				label: 'Descripción del Gasto',
				fieldname: 'description',
				fieldtype: 'Small Text',
				reqd: 1,
				placeholder: "Compra de Combustible"
			},
			{
				fieldtype: "Section Break",
			},
			{
				label: 'Tipo Bienes y Servicios Comprados',
				fieldname: 'tipo_bienes_y_servicios_comprados',
				fieldtype: 'Select',
				reqd: 1,
				options: `
01-GASTOS DE PERSONAL
02-GASTOS POR TRABAJOS, SUMINISTROS Y SERVICIOS
03-ARRENDAMIENTOS
04-GASTOS DE ACTIVOS FIJO
05 -GASTOS DE REPRESENTACIÓN
06 -OTRAS DEDUCCIONES ADMITIDAS
07 -GASTOS FINANCIEROS
08 -GASTOS EXTRAORDINARIOS
09 -COMPRAS Y GASTOS QUE FORMARAN PARTE DEL COSTO DE VENTA
10 -ADQUISICIONES DE ACTIVOS
11- GASTOS DE SEGUROS`,
				default: `02-GASTOS POR TRABAJOS, SUMINISTROS Y SERVICIOS`
			},
			{
				fieldtype: "Section Break",
			},
			{
				label: 'Cuenta de Gastos',
				fieldname: 'expense_account',
				fieldtype: 'Link',
				options: 'Account',
				reqd: 1,
				get_query: () => {
					return {
						filters: {
							root_type: 'Expense',
							company: doc.company,
							is_group: 0,
						}
					}
				}
			},
			{
				fieldtype: "Column Break",
			},
			{
				label: 'Centro de Costos',
				fieldname: 'cost_center',
				fieldtype: 'Link',
				options: 'Cost Center',
				reqd: 0,
				get_query: () => {
					return {
						filters: {
							company: doc.company,
							is_group: 0,
						}
					}
				}
			},
			{
				label: 'Project',
				fieldname: 'project',
				fieldtype: 'Link',
				options: 'Project',
				reqd: 0,
			},
			{
				fieldtype: "Section Break",
			},
			{
				label: 'Monto Total (incluyendo impuestos)',
				fieldname: 'total_amount',
				fieldtype: 'Currency',
				reqd: 1
			},
			{
				label: 'Método de Pago',
				fieldname: 'payment_mode',
				fieldtype: 'Link',
				options: "Mode of Payment",
				reqd: 1
			}
		], ({
			reference_date,
			reference_number,
			description,
			expense_account,
			cost_center,
			project,
			total_amount,
			payment_mode
		}) => {
			_update_pinv_with_minor_expenses_details(frm, {
				reference_date,
				reference_number,
				description,
				expense_account,
				cost_center,
				project,
				total_amount,
				payment_mode
			});
		}, "Detalles de Gastos Menores", "Guardar");
	}

	function _update_pinv_with_minor_expenses_details(frm, {
		reference_date,
		reference_number,
		description,
		expense_account,
		cost_center,
		project,
		total_amount,
		payment_mode
	}) {
		frappe.run_serially([
			async function() {
				await frm.set_value("is_paid", 1);
			},
			async function() {
				await frm.set_value("currency", "DOP");
			},
			async function() {
				await frm.set_value("bill_date", reference_date);
			},
			async function() {
				await frm.set_value("bill_no", reference_number);
			},
			async function() {
				await frm.set_value("cost_center", cost_center);
			},
			async function() {
				await frm.set_value("project", project);
			},
			async function() {
				frm.add_child("items", {
					item_code: "",
					item_name: description,
					description: description,
					uom: "ud(s)",
					conversion_factor: 1,
					qty: 1,
					rate: total_amount,
					amount: total_amount,
					cost_center: cost_center,
					project: project,
					expense_account: expense_account,
					
				});
			},
			async function() {
				await frm.set_value("paid_amount", total_amount);
			},
			async function() {
				await frm.set_value("mode_of_payment", payment_mode);
			},
			async function() {
				await frm.save();
			},
		]);
	}

	function _validate_rnc(frm) {
		const { doc } = frm;

		if (doc.tax_id) {
			let len = doc.tax_id.length;
			
			if (![9, 11].includes(len)) {
				frappe.msgprint(`El RNC/Cedula ingresados tiene <b>${len}</b> caracteres favor verificar, deben ser 9 u 11.`);
				frappe.validated = false;
				return false; 
			}
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

		supplier(frm) {
			const { doc } = frm;

			if (!doc.supplier) {
				return ; // die young if no supplier
			}

			if (doc.supplier === doc.company) {
				_prompt_for_minor_expesenses_details(frm);
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