// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

export default function() {
	const { document: doc } = this;

	let form_data = {
		porcentaje_adicional: 5, // 5% default
	};

	try {
		const _form_data = JSON.parse(doc.data || "{}");
		if (
			Object.keys(_form_data).length > 0
		) {
			form_data = {
				...form_data,
				..._form_data,
			};
		}
	} catch (e) {
		console.error(e);
	}

	return {
		quantity: 5,
		rate: 3,
		amount: 0,
		doc: this.document,
		raw_material_specs: {},

		// misc
		selecting_ink: false,
		ink_colors: [],

		// Cost Estimation Fields
		form_data, // let this one be dynamic
		// form_data: {
		//   ancho_montaje: 0,
		//   alto_montaje: 0,
		//   ancho_material: 0,
		//   alto_material: 0,
		//   ancho_producto: 0,
		//   alto_producto: 0,
		//   tecnologia: "",

		//   // colors
		//   colores_procesos_tiro: 0,
		//   colores_pantones_tiro: 0,
		//   colores_especiales_tiro: 0,
		//   colores_procesos_retiro: 0,
		//   colores_pantones_retiro: 0,
		//   colores_especiales_retiro: 0,
		// },
	};
};
