// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

export default {
	fetch_raw_material_specs() {
		this.material_controller.fetch_raw_material_specs(
			this.frm.doc.raw_material,
		);
	},
	update_data() {
		const data = JSON.stringify(this.form_data, null, 4);
		this.frm.set_value("data", data);
	},
	after_color_select(fieldname, value) {
		this.form_data[fieldname] = value;
		this.update_data();
	},
	handle_relieve_dimension_change(index, width, height) {
		this.form_data[`ancho_elemento_relieve_${index}`] = width;
		this.form_data[`alto_elemento_relieve_${index}`] = height;
		this.update_data();
	},
	select_ink_color(side, fieldname) {
		const self = this;
		const method = {
			"Tiro": "get_selected_ink_colors_in_front_side",
			"Retiro": "get_selected_ink_colors_in_back_side",
		}[side];

		const fields = [
			{
				fieldname: "ink_color",
				fieldtype: "Link",
				options: "Ink Color",
				label: __("Ink Color"),
				reqd: 1,
				filters: { 
					name: ["not in", self[method]()],
				},
			},
		];

		function callback(values) {
			const { ink_color } = values;

			self.form_data[fieldname] = ink_color;
			self.update_data();

			self.fetch_ink_color(fieldname, ink_color);
		};

		const title = __("Select Ink Color");
		const primary_label = __("Select");

		frappe.prompt(fields, callback, title, primary_label);
	},
	select_product_type() {
		const self = this;
		const fields = [
			{
				fieldname: "product_type",
				fieldtype: "Link",
				options: "Product Type",
				label: __("Product Type"),
				default: self.form_data.tipo_de_producto,
				reqd: 1,
			},
		];

		function callback(values) {
			const { product_type } = values;

			self.form_data.tipo_de_producto = product_type;
			self.update_data();

			self.fetch_product_type_details(product_type);
		};

		const title = __("Select Product Type");
		const primary_label = self.form_data.tipo_de_producto? __("Select"): __("Update");

		frappe.prompt(fields, callback, title, primary_label);
	},
	get_selected_ink_colors_in_front_side() {
		if (!this.form_data) {
			return [];
		}

		if (!this.form_data.cantidad_de_tintas_tiro) {
			return [];
		}

		const selected_ink_colors = [];
		for (let i = 1; i <= this.form_data.cantidad_de_tintas_tiro; i++) {
			const fieldname = `tinta_seleccionada_tiro_${i}`;
			const ink_color = this.form_data[fieldname];

			if (ink_color) {
				selected_ink_colors.push(ink_color);
			}
		}

		return selected_ink_colors;
	},
	get_selected_ink_colors_in_back_side() {
		if (!this.form_data) {
			return [];
		}

		if (!this.form_data.cantidad_de_tintas_retiro) {
			return [];
		}

		const selected_ink_colors = [];
		for (let i = 1; i <= this.form_data.cantidad_de_tintas_retiro; i++) {
			const fieldname = `tinta_seleccionada_retiro_${i}`;
			const ink_color = this.form_data[fieldname];

			if (ink_color) {
				selected_ink_colors.push(ink_color);
			}
		}

		return selected_ink_colors;
	},
	fetch_ink_color(field, ink_color) {
		const self = this;
		const doctype = "Ink Color";
		const filters = {
			name: ink_color,
		};
	
		const fieldname = "hexadecimal_color";
		function callback({ hexadecimal_color }) {
			self.form_data[`hex_${field}`] = hexadecimal_color;
			self.update_data();
		}
	
		const parent_doc = null;
		frappe.db.get_value(doctype, filters, fieldname, callback, parent_doc);
	},
	fetch_product_type_details(product_type) {
		const method = "powerpro.manufacturing_pro.doctype.cost_estimation.client.get_product_type_details";
		function callback({ message}) {
			console.log({ message });
		};

		const args = { 
			product_type,
		};

		function callback({ message }) {
			console.log({ message });
		};

		const freeze = true;
		const freeze_message = "Loading Product Type details";
		frappe.call({ method, args, callback, freeze, freeze_message });
			
	},
};