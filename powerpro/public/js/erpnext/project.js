// Copyright (c) 2025, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.provide("powerpro.masks");

{

	function refresh(frm) {
		_set_qty_mask(frm);
		_set_queries(frm);
		_render_docfields(frm);
	}

	function project_template(frm) {
		_render_docfields(frm);
	}

	function sales_order(frm) {
		frm.set_value("producto", "");
	}


	function _render_docfields(frm) {
		const { doc } = frm;

		// if (!doc.project_template) {
		// 	return ; // Do nothing
		// }

		frappe.call({
			method: "powerpro.controllers.project_template.get_project_docfields",
			args: {
				"project_template_id": cur_frm.doc.project_template,
			},
			callback({ message: docfields }) {
				for (const docfield of docfields) {
					const { fieldname, read_only, reqd, hidden } = docfield;

					for (
						const { property, value } of [
							{ property: "read_only", value: read_only },
							{ property: "reqd", value: reqd },
							{ property: "hidden", value: hidden },
						]
					) {
						frm.set_df_property(fieldname, property, value);
					}
				}
			},
		});
	}

	function _set_qty_mask(frm) {
		// function formatNumberInput(input) {
		// 	let value = input.value.replace(/\D/g, ''); // Elimina todo lo que no sea dígito
		// 	value = new Intl.NumberFormat('es-DO').format(value); // Formato latino (puntos para miles)
		// 	input.value = value;
		// }

		// powerpro.masks.formatNumberInput = formatNumberInput;

		const field = frm.get_field("cantidad_a_producir");
		const { $input } = field;
		// field.$input.attr("oninput", "powerpro.masks.formatNumberInput(this)");


		async function formatNumber(value) {
			await frappe.timeout(.1);
			// Elimina todo excepto dígitos y el punto decimal
			value = value.replace(/[^0-9.]/g, '');
			if (!value) return '';

			const parts = value.split('.');
			const integerPart = parts[0];
			const decimalPart = parts[1] || '';

			// Formatea la parte entera al estilo es-DO
			const formattedInt = new Intl.NumberFormat('es-DO').format(Number(integerPart));

			return decimalPart ? `${formattedInt}.${decimalPart}` : formattedInt;
		}

		async function formatNumberInput(input) {
			const cursorPos = input.selectionStart;
			input.value = await formatNumber(input.value);
			// Opcional: restaurar posición del cursor
			input.setSelectionRange(cursorPos, cursorPos);
		}

		// Aplica formato en tiempo real
		$input[0].addEventListener('input', function () {
			formatNumberInput(this);
		});


		// const input = $input[0];
		// input.value = formatNumber(input.value);
	}

	function _set_queries(frm) {
		frappe.run_serially([
			() => {
				const fieldname = "project_template";
				const get_query = function () {
					const filters = {
						"project_type": frm.doc.project_type || "",
					};

					return { filters };
				};

				frm.set_query(fieldname, get_query);
			},
			() => {
				const fieldname = "producto";
				const get_query = function () {
					const query = "powerpro.controllers.queries.get_sales_order_items";
					const filters = {
						"sales_order": frm.doc.sales_order || "",
					};

					if (!frm.doc.sales_order) {
						return { filters };
					}

					return { query, filters };
				};

				frm.set_query(fieldname, get_query);
			},
		]);
	}

	frappe.ui.form.on("Project", {
		refresh,
		sales_order,
		project_template,
	});
}