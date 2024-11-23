// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

let power_pro_settings;
let loading_power_pro_settings = false;

export default {
	is_new() {
		return this.frm.is_new();
	},
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
				reqd: 0,
			},
		];

		function callback(values) {
			const { product_type } = values;

			self.form_data.tipo_de_producto = product_type;
			self.update_data();

			self.fetch_product_type_details(product_type);
		};

		const title = __("Select Product Type");
		const primary_label = self.form_data.tipo_de_producto? __("Update"): __("Select");

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
		const self = this;
		const method = "powerpro.manufacturing_pro.doctype.cost_estimation.client.get_product_type_details";
		const args = { 
			product_type,
		};

		function callback({ message: operations }) {
			Object.assign(self.form_data, { operations });
			self.update_data();
		};

		const freeze = true;
		const freeze_message = "Loading Product Type details";

		if (product_type) {
			frappe.call({ method, args, callback, freeze, freeze_message });
		}
	},
	load_power_pro_settings() {
		const self = this;
		const method = "powerpro.controllers.assets.get_power_pro_settings";
		const args = {
			// empty
		};
		
		function callback({ message: powerpro_settings }) {
			self.powerpro_settings = powerpro_settings;
			loading_power_pro_settings = false;

			// update global variable
			power_pro_settings = powerpro_settings;
		}

		// for some reason, this method is being called twice.
		if (!loading_power_pro_settings) {
			loading_power_pro_settings = true;
			frappe.call({ method, args, callback });
		}
	},
	load_coating_type_options() {
		const self = this;
		const method = "powerpro.controllers.assets.get_coating_type_options";
		const args = {
			// empty
		};
		
		function callback({ message }) {
			for (const option of message) {
				self.select_options["tipo_barnizado"]
					.push({ value: option });
			}
		};

		frappe.call({ method, args, callback });
	},
	load_lamination_type_options() {
		const self = this;
		const method = "powerpro.controllers.assets.get_lamination_type_options";
		const args = {
			// empty
		};
		
		function callback({ message }) {
			for (const option of message) {
				self.select_options["tipo_laminado"]
					.push({ value: option })
				;
			}
		};

		frappe.call({ method, args, callback });
	},
	load_gluing_type_options() {
		const self = this;
		const method = "powerpro.controllers.assets.get_gluing_type_options";
		const args = {
			// empty
		};
		
		function callback({ message }) {
			for (const option of message) {
				self.select_options["tipo_pegado"]
					.push({ value: option })
				;
			}
		};

		frappe.call({ method, args, callback });
	},
	load_foil_color_options() {
		const self = this;
		const method = "powerpro.controllers.assets.get_foil_color_options";
		const args = {
			// empty
		};
		
		function callback({ message }) {
			for (const option of message) {
				self.select_options["color_lamina"]
					.push({ value: option })
				;
			}
		};

		frappe.call({ method, args, callback });
	},
	validate_and_set_margin_of_utility(value, set_value) {
		const self = this;
		// const { powerpro_settings: settings } = this;
		const settings = power_pro_settings;

		if (
			!settings
			|| typeof settings.min_margin !== "number"
			|| typeof settings.max_margin !== "number"
		) {
			self.form_data.margen_de_utilidad = value;
			return ; // do nothing else
		}

		const { min_margin, max_margin } = settings;

		// validate the value
		if (value > max_margin) {
			frappe.msgprint(__("The value is above the maximum margin of utility"));
			self.form_data.margen_de_utilidad = max_margin;
			set_value(max_margin);
		} else if (value < min_margin) {
			frappe.msgprint(__("The value is below the minimum margin of utility"));
			set_value(min_margin);
			self.form_data.margen_de_utilidad = min_margin;
		} else {
			self.form_data.margen_de_utilidad = value;
		}
	},
	mount_product_type_field() {
		const self = this;

		let internal = false;
		this.product_type_field = frappe.ui.form.make_control({
			df: {
				fieldtype: "Link",
				fieldname: "tipo_de_producto",
				options: "Product Type",
				label: __("Product Type"),
				reqd: 1,
				change() {
					if (internal) {
						internal = false;
						return ; // do nothing
					}

					self.form_data.tipo_de_producto = this.value;
					self.update_data();
					self.frm.set_value("product_type", this.value);
				},
			},
			render_input: true,
			parent: self.$refs.tipo_de_producto,
		});

		internal = true;
		this.product_type_field.set_value(self.form_data.tipo_de_producto);
	},
	mount_raw_material_field() {
		const self = this;

		let internal = false;
		this.raw_material_field = frappe.ui.form.make_control({
			df: {
				fieldtype: "Link",
				fieldname: "raw_material",
				options: "Raw Material",
				label: __("Raw Material"),
				reqd: 1,
				change() {
					if (internal) {
						internal = false;
						return ; // do nothing
					}

					self.form_data.material = this.value;
					self.update_data();
					self.frm.set_value("raw_material", this.value);
				},
			},
			render_input: true,
			parent: this.$refs.material,
		});

		internal = true;
		this.raw_material_field.set_value(self.form_data.material);
	},
};