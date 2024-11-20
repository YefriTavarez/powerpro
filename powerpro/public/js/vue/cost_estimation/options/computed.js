// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

export default {
	// selected_ink_colors() {
	// 	// return selected_ink_colors;
	// },
	cantidad_de_producto_con_adicional() {
		return (
			flt(this.form_data.cantidad_de_producto) 
			* (
				(
					flt(this.form_data.porcentaje_adicional) / 100.000
				) + 1
			)
		).toLocaleString();
	}
}