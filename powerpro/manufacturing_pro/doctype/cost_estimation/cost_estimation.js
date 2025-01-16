// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt

{
	frappe.provide("power.ui.cost_estimation");

	function _setup_vue(frm) {
		frappe.require([
			"powerpro.bundle.js",
		], function() {
			_refresh_vue(frm);
		});
	}

	async function _refresh_vue(frm) {
		await frappe.timeout(0.5);
		const selector = `div[data-fieldname="cost_estimation_app"]`;
			
		if (!power.ui.CostEstimationApp) {
			jQuery(
				selector
			).html(
				`<p class="text-muted" style="color: rgb(181, 42, 42) !important">
					${__("Error while loading Cost Estimation")}
				</p>`
			);

			frappe.show_alert({
				message: __("Vue.CostEstimationApp is not available!"),
				indicator: "red",
			});

			return ; // exit
		}

		power.ui.cost_estimation = new power.ui.CostEstimationApp(frm, selector);
	}

	function _autoset_expires_on({ frm, force = false }) {
		// sets the expires on based on the created_on (if set)
		// otherwise, sets the expires on based on the current date + 30 days
		// if not created_on is set and created_on is set and force is false, then do nothing
		// if created_on is set and force is true, then set the expires_on based on the created_on

		const { doc } = frm;
		const { add_days } = frappe.datetime;

		if (!doc.created_on) {
			if (force) {
				doc.expires_on = add_days(frappe.datetime.now_date(), 30);
			}
		} else {
			doc.expires_on = add_days(doc.created_on, 30);
		}

		frm.refresh_field("expires_on");
	}

	function _validate_expires_on(frm) {
		// validate expires_on is never less than created_on (if set)
		// if created_on is not set, then let's make sure it is not less than the current date

		const { doc } = frm;

		if (!doc.created_on) {
			if (doc.expires_on < frappe.datetime.now_date()) {
				frappe.msgprint(__("Expires On cannot be less than the current date!"));
			}
		} else if (doc.expires_on < doc.created_on) {
			frappe.msgprint(__("Expires On cannot be less than Created On!"));
		}
	}

	function setup(frm) {
		_setup_vue(frm);
	}

	function refresh(frm) {
		_refresh_vue(frm);
		_add_custom_buttons(frm);
		_setup_intro(frm);
	}

	function raw_material(frm) {
		const { cost_estimation } = power.ui;
		cost_estimation.fetch_raw_material_specs();
	}

	function onload_post_render(frm) {
		_autoset_expires_on({ frm });
	}


	// VALIDATE THE VUE FORM
	function validate(frm) {
		/* Validaciones de campos obligatorios:
		tipo_de_producto
		material
		cantidad_montaje
		cantidad_de_producto
		porcentaje_adicional
		ancho_producto
		alto_producto
		ancho_montaje
		alto_montaje
		ancho_material
		alto_material
		tecnologia
		cantidad_de_tintas_tiro
			tinta_seleccionada_tiro_1 #*
			tinta_seleccionada_tiro_2 #*
			tinta_seleccionada_tiro_3 #*
			tinta_seleccionada_tiro_4 #*
			tinta_seleccionada_tiro_5 #*
			tinta_seleccionada_tiro_6 #*
			tinta_seleccionada_tiro_7 #*
			tinta_seleccionada_tiro_8 #*
		cantidad_de_tintas_retiro
			tinta_seleccionada_retiro_1 #*
			tinta_seleccionada_retiro_2 #*
			tinta_seleccionada_retiro_3 #*
			tinta_seleccionada_retiro_4 #*
			tinta_seleccionada_retiro_5 #*
			tinta_seleccionada_retiro_6 #*
			tinta_seleccionada_retiro_7 #*
			tinta_seleccionada_retiro_8 #*
		incluye_barnizado
			tipo_barnizado *
	
		incluye_laminado
			tipo_laminado *
	
		incluye_relieve
			tipo_de_relieve *
			tipo_de_material_relieve *
			cantidad_de_elementos_en_relieve *
				ancho_elemento_relieve_1 #*
				ancho_elemento_relieve_2 #*
				ancho_elemento_relieve_3 #*
				ancho_elemento_relieve_4 #*
				ancho_elemento_relieve_5 #*
	
				alto_elemento_relieve_1 #*
				alto_elemento_relieve_2 #*
				alto_elemento_relieve_3 #*
				alto_elemento_relieve_4 #*
				alto_elemento_relieve_5 #*
	
	
		incluye_troquelado
			troquel_en_inventario #
		incluye_utilidad
			tipo_utilidad *
	
			cinta_doble_cara_cantidad_de_puntos *
			cinta_doble_cara_ancho_punto *
			cinta_doble_cara_alto_punto *
	
		incluye_pegado
			tipo_pegado *
		tipo_de_empaque *
	
		margen_de_utilidad *
		*/
	
		const form_data = JSON.parse(frm.doc.data);
	
		if (!form_data.tipo_de_producto) {
			frappe.msgprint('El campo "Tipo de producto" es obligatorio');
			frappe.validated = false;
		}
	
		if (!form_data.material) {
			frappe.msgprint('El campo "Material" es obligatorio');
			frappe.validated = false;
		}
	
		if (!form_data.cantidad_montaje) {
			frappe.msgprint('El campo "Cantidad de montaje" es obligatorio');
			frappe.validated = false;
		}
	
		if (!form_data.cantidad_de_producto) {
			frappe.msgprint('El campo "Cantidad de producto" es obligatorio');
			frappe.validated = false;
		}
	
		if (!form_data.porcentaje_adicional && form_data.porcentaje_adicional !== 0) {
			frappe.msgprint('El campo "Porcentaje adicional" es obligatorio');
			frappe.validated = false;
		}
	
		if (!form_data.ancho_producto) {
			frappe.msgprint('El campo "Ancho de producto" es obligatorio');
			frappe.validated = false;
		}
	
		if (!form_data.alto_producto) {
			frappe.msgprint('El campo "Alto de producto" es obligatorio');
			frappe.validated = false;
		}
	
		if (!form_data.ancho_montaje) {
			frappe.msgprint('El campo "Ancho de montaje" es obligatorio');
			frappe.validated = false;
		}
	
		if (!form_data.alto_montaje) {
			frappe.msgprint('El campo "Alto de montaje" es obligatorio');
			frappe.validated = false;
		}
	
		if (!form_data.ancho_material) {
			frappe.msgprint('El campo "Ancho de material" es obligatorio');
			frappe.validated = false;
		}
	
		if (!form_data.alto_material) {
			frappe.msgprint('El campo "Alto de material" es obligatorio');
			frappe.validated = false;
		}
	
		if (!form_data.tecnologia) {
			frappe.msgprint('El campo "Tecnología" es obligatorio');
			frappe.validated = false;
		}
	
		if (!form_data.cantidad_de_tintas_tiro && form_data.cantidad_de_tintas_tiro !== 0) {
			frappe.msgprint('El campo "Cantidad de Tintas en el Tiro" es obligatorio');
			frappe.validated = false;
		}
	
		// depende de la cantidad de tintas tiro
		for (let i = 1; i <= cint(form_data.cantidad_de_tintas_tiro); i++) {
			if (!form_data[`tinta_seleccionada_tiro_${i}`]) {
				frappe.msgprint(`El campo "Tinta ${i} en el Tiro" es obligatorio`);
				frappe.validated = false;
			}
		}
	
		if (!form_data.cantidad_de_tintas_retiro && form_data.cantidad_de_tintas_retiro !== 0) {
			frappe.msgprint('El campo "Cantidad de Tintas en el Retiro" es obligatorio');
			frappe.validated = false;
		}
	
		// depende de la cantidad de tintas retiro
		for (let i = 1; i <= cint(form_data.cantidad_de_tintas_retiro); i++) {
			if (!form_data[`tinta_seleccionada_retiro_${i}`]) {
				frappe.msgprint(`El campo "Listado de Tintas en el Retiro ${i}" es obligatorio`);
				frappe.validated = false;
			}
		}
	
		if (form_data.incluye_barnizado && !form_data.tipo_barnizado) {
			frappe.msgprint('El campo "Tipo de Barnizado" es obligatorio');
			frappe.validated = false;
		}
	
		if (form_data.incluye_laminado && !form_data.tipo_laminado) {
			frappe.msgprint('El campo "Tipo de Laminado" es obligatorio');
			frappe.validated = false;
		}
	
		if (form_data.incluye_relieve) {
			if (!form_data.tipo_de_relieve) {
				frappe.msgprint('El campo "Tipo de Relieve" es obligatorio');
				frappe.validated = false;
			}
	
			if (form_data.tipo_de_relieve === "Estampado" && !form_data.tipo_de_material_relieve) {
				frappe.msgprint('El campo "Color de Lamina en Relieve" es obligatorio');
				frappe.validated = false;
			}
	
			if (!form_data.cantidad_de_elementos_en_relieve) {
				frappe.msgprint('El campo "Cantidad de Elementos en Relieve" es obligatorio');
				frappe.validated = false;
			}
	
			// depende de la cantidad de elementos en relieve
			for (let i = 1; i <= cint(form_data.cantidad_de_elementos_en_relieve); i++) {
				if (!form_data[`ancho_elemento_relieve_${i}`]) {
					frappe.msgprint(`El campo "Ancho de Elemento ${i} en Relieve" es obligatorio`);
					frappe.validated = false;
				}
	
				if (!form_data[`alto_elemento_relieve_${i}`]) {
					frappe.msgprint(`El campo "Alto de Elemento ${i} en Relieve" es obligatorio`);
					frappe.validated = false;
				}
			}
		}
	
		// if (form_data.incluye_troquelado && !form_data.troquel_en_inventario) {
		// 	frappe.msgprint('El campo "Troquel en Inventario" es obligatorio');
		// 	frappe.validated = false;
		// }
	
		if (form_data.incluye_utilidad) {
			if (!form_data.tipo_utilidad) {
				frappe.msgprint('El campo "Tipo de Utilidad" es obligatorio');
				frappe.validated = false;
			}
	
			if (!form_data.cinta_doble_cara_cantidad_de_puntos) {
				frappe.msgprint('El campo "Cantidad de Puntos en Utilidad" es obligatorio');
				frappe.validated = false;
			}
	
			if (!form_data.cinta_doble_cara_ancho_punto) {
				frappe.msgprint('El campo "Ancho de Punto en Utilidad" es obligatorio');
				frappe.validated = false;
			}
	
			if (!form_data.cinta_doble_cara_alto_punto) {
				frappe.msgprint('El campo "Alto de Punto en Utilidad" es obligatorio');
				frappe.validated = false;
			}
		}
	
		if (form_data.incluye_pegado && !form_data.tipo_pegado) {
			frappe.msgprint('El campo "Tipo de Pegado" es obligatorio');
			frappe.validated = false;
		}
	
		if (!form_data.tipo_de_empaque) {
			frappe.msgprint('El campo "Tipo de Empaque" es obligatorio');
			frappe.validated = false;
		}
	}

	function created_on(frm) {
		// update expires_on
		_autoset_expires_on({ frm, force: true });
	}

	function expires_on(frm) {
		_validate_expires_on(frm);
	}

	function data(frm) {
		// ToDo: validate data
	}

	function _add_custom_buttons(frm) {
		if (frm.is_new()) {
			// buttons for new documents
			_add_load_from_sku_button(frm);
		} else {
			if (frm.doc.docstatus === 0) {
				// buttons for draft documents
			} else if (frm.doc.docstatus === 1) {
				// buttons for submitted documents
				_add_create_sku_button(frm);
			} else {
				// buttons for cancelled documents
			}
		}

		// always on buttons
	}

	function _setup_intro(frm) {
		const { doc } = frm;
		
		frm.set_intro(); // clear intro
		if (doc.docstatus === 2) {
			return ; // exit
		}

		const { __onload: data } = doc;

		if (!data) {
			return ; // exit
		}

		if (data.smart_hash_exist) {
			frm.set_intro(
			`${__("There is already an SKU for with this exact data.")}<br>
				<button class="btn btn-info btn-xs" onclick="frappe.utils.copy_to_clipboard('${data.item_id}')">${__("Copy SKU")}</button>
				${__("or go to the Item itself by clicking here")} <a href="/app/item/${data.item_id}">${data.item_id}</a>`, "blue");
		}
	}

	function _add_load_from_sku_button(frm) {
		const label = __("SKU");
		function action(event) {
			_show_load_from_sku_popup(frm);
		}
		const parent = __("Fetch From");
		frm.add_custom_button(label, action, parent);
	}

	function _show_load_from_sku_popup(frm) {
		const fields = [
			{
				fieldtype: "Link",
				fieldname: "item",
				label: __("Item"),
				options: "Item",
				description: __("Please select an Item to load from"),
				reqd: 1,
				get_query: {
					reference_type: frm.doctype,
				}
			},
		];

		function callback({ item }) {
			_load_estimation_from_sku(frm, item);
		}

		const title = __("Load from Item");
		const primary_label = __("Load");
		
		frappe.prompt(fields, callback, title, primary_label);
	}

	function _add_create_sku_button(frm) {
		const { doc } = frm;

		if (!frm.is_dirty() && !doc.__onload.smart_hash_exist) {
			frm.add_custom_button(
				__("SKU"),
				() => {
					const method = "create_sku";
					const args = {
						// no-args
					};
					
					frm.call(method, args)
						.then(function(response) {
							const { message } = response;
				
							if (message) {
								frappe.confirm(`
									${__("Here is the SKU")} <strong>${message}</strong>
									<button class="btn btn-info" onclick="frappe.utils.copy_to_clipboard('${message}')">
										${__("Copy to Clipboard")}
									</button>
									<br>${__("Do you want me to take you there?")}
								`, () => {
									frappe.set_route("Form", "Item", message);
								}, () => {
									frappe.show_alert({
										message: __("Alright... let's be productive, then!"),
										indicator: "green",
									});
								});
				
								frappe.show_alert({
									message,
									indicator: "green",
								});

								frm.reload_doc();
							} else {
								frappe.show_alert({
									message: __("SKU not created!"),
									indicator: "red",
								});
				
								frappe.confirm(
									__("Would you like to try again?"),
									() => dialog.show(),
									() => frappe.show_alert(__("Okay!")),
								);
							}
						}, function(exec) {
							frappe.show_alert({
								message: __("SKU not created!"),
								indicator: "red",
							});
				
							frappe.confirm(
								__("Would you like to try again?"),
								() => dialog.show(),
								() => frappe.show_alert(__("Okay!")),
							);
						});
				},
				__("Create")
			);
		}
	}

	function _load_estimation_from_sku(frm, sku) {
		const doctype = "Item";
		const name = sku;
		const fieldname = "product_details";
		function callback({ product_details: value }) {
			function __onerror() {
				frappe.msgprint(
					__("Woops! It looks like this SKU was created using an older version of the Cost Estimation.")
				);
			}

			let object = null;

			if (!value) {
				__onerror();
				return ; // exit
			} else {

				try {
					object = JSON.parse(value);
				} catch (error) {
					__onerror();
					return ; // exit
				}

				if (Object.keys(value).length === 0) {
					__onerror();
					return ; // exit
				}
			}
			
			frm.set_value("product_type", object.tipo_de_producto);
			frm.set_value("raw_material", object.material);
			
			frm.set_value("data", value);
			_refresh_vue(frm);

			frappe.show_alert({
				message: __("Estimation loaded!"),
				indicator: "green",
			});
		}
		frappe.db.get_value(doctype, name, fieldname, callback);
	}

	frappe.ui.form.on("Cost Estimation", {
		setup,
		refresh,
		onload_post_render,
		validate,
		raw_material,
		created_on,
		expires_on,
		data,
	});
}