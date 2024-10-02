frappe.ui.form.on("Purchase Invoice", {
	
	refresh(frm){
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
	include_isr(frm){
		frm.trigger("calculate_isr");
		$.map(["retention_rate", "retention_type"], field => {
			frm.set_df_property(field, 'reqd', frm.doc.include_isr);
		})
	},
	isr_rate(frm){
		frm.trigger("calculate_isr");
	},
	include_retention(frm){
		frm.set_df_property("retention_rate", 'reqd', frm.doc.include_retention);

		frm.trigger("calculate_retention");
		frm.trigger("update_taxes_amount")
	},
	retention_rate(frm){
		frm.trigger("calculate_retention");
		// frm.trigger("update_taxes_amount")
	
	},
	update_taxes_amount(frm) {
		const { doc } = frm;
		if (!doc.include_retention && !doc.include_isr) return;
		let retencion_rete;
		if (doc.retention_rate == '30%') {
				retencion_rete = 30
			}
		if (frm.doc.retention_rate == '100%') {
				retencion_rete = 100
			}
	
		frm.doc.taxes.map((row)=>{
			if (doc.include_retention && !doc.include_isr) {
				const itbis_rate = row.rate * (100 - retencion_rete) / 100;
				frappe.model.set_value("Purchase Taxes and Charges", row.name, "rate", itbis_rate)
				frm.refresh_field("taxes")
			} else if (doc.include_retention && doc.include_isr) {
				const itbis_rate = row.rate * (100 - (retencion_rete - doc.isr_rate)) / 100;
				frappe.model.set_value("Purchase Taxes and Charges", row.name, "rate", itbis_rate)
				frm.refresh_field("taxes")
			}
		})
	},
	calculate_retention(frm){
		if (!frm.doc.include_retention || !frm.doc.total_taxes_and_charges || !frm.doc.retention_rate)
			frm.set_value("retention_amount", 0);

		let retention_rate = 0;
		if (frm.doc.retention_rate == '2%')
			retention_rate = 0.02;

		if (frm.doc.retention_rate == '30%')
			retention_rate = 0.30;
		
		if (frm.doc.retention_rate == '100%')
			retention_rate = 1;
		
		frm.set_value("retention_amount", frm.doc.total_taxes_and_charges * retention_rate);
	},
	calculate_isr(frm){
		if (!frm.doc.include_isr || !frm.doc.total || !frm.doc.isr_rate)
			frm.set_value("isr_amount", 0);
		let amount = frm.doc.total * (frm.doc.isr_rate / 100);
		frm.set_value("isr_amount", amount);
	}
});

