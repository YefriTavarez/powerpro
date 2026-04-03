// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.provide("power.ui");
frappe.provide("power.utils");

const { round_to_nearest_eighth } = power.utils;

power.ui.CreateMaterialSKU = function(docname) {
	let dialog;
	let item_group_details;
	let doc;
	let selected_parent_material;
	let derived_dimension_options = new Map();

	const DERIVED_DIMENSION_FACTORS = [
		{ label: "1", value: 1 },
		{ label: "1/2", value: 0.5 },
		{ label: "1/3", value: 1 / 3 },
		{ label: "1/4", value: 0.25 },
	];
	const MIN_DERIVED_SIDE = 10;
	const DIMENSION_MATCH_TOLERANCE = 0.001;

	const url = "/api/method/powerpro.controllers.assets.item_group.get_all_item_groups";
	frappe.dom.freeze(__("Cargando..."));
	fetch(url)
		.then(response => response.json())
		.then(({ message }) => {
			item_group_details = message;
		});
	
	fetch(`/api/resource/Raw Material/${docname}`)
		.then(response => response.json())
		.then(({ data }) => {
			doc = data;

			// const description_field = dialog.get_field("material_description")

			// description_field.$wrapper.html(`
			// 	<p class="text-muted">Material</p>
			// 	<h3>${doc.description}</h3>
			// `);

			// if (doc.base_material === "Paper") {
				
			// }
			_render_dialog(doc);
		})
		.finally(() => {
			frappe.dom.unfreeze();
		});

	function to_number(value) {
		const number = parseFloat(value);

		return Number.isFinite(number) ? number : null;
	}

	function normalize_dimension(value) {
		const number = to_number(value);

		if (number === null) {
			return null;
		}

		return Number(round_to_nearest_eighth(number));
	}

	function format_dimension(value) {
		const number = normalize_dimension(value);

		if (number === null) {
			return "";
		}

		return number.toFixed(3).replace(/\.?0+$/, "");
	}

	function normalize_dimension_pair(first, second) {
		const dimensions = [normalize_dimension(first), normalize_dimension(second)];

		if (dimensions.includes(null)) {
			return [];
		}

		return dimensions.sort((left, right) => right - left);
	}

	function dimensions_match(left, right) {
		return Math.abs(left - right) <= DIMENSION_MATCH_TOLERANCE;
	}

	function is_derived_sheet(values = null) {
		const material_format = values?.material_format ?? dialog?.get_value("material_format");
		const standard_sheet_size = values?.standard_sheet_size ?? dialog?.get_value("standard_sheet_size");

		return material_format === "Sheet" && standard_sheet_size === "Derivado";
	}

	function get_side_candidates(side) {
		const seen = new Set();

		return DERIVED_DIMENSION_FACTORS.reduce((accumulator, factor) => {
			const dimension = normalize_dimension(side * factor.value);

			if (dimension === null || dimension < MIN_DERIVED_SIDE || seen.has(dimension)) {
				return accumulator;
			}

			seen.add(dimension);
			accumulator.push({
				dimension,
				factor: factor.label,
				is_original: factor.value === 1,
			});

			return accumulator;
		}, []);
	}

	function build_roll_parent_options(parent_material) {
		return get_side_candidates(parent_material.roll_width).map(candidate => {
			const label = candidate.is_original
				? `${format_dimension(candidate.dimension)} in (${__("Ancho Completo del Rollo")})`
				: `${format_dimension(candidate.dimension)} in (${__("Ancho del Rollo")} x ${candidate.factor})`;

			return {
				label,
				type: "Roll",
				side: candidate.dimension,
			};
		});
	}

	function build_sheet_parent_options(parent_material) {
		const width_candidates = get_side_candidates(parent_material.sheet_width);
		const height_candidates = get_side_candidates(parent_material.sheet_height);
		const seen = new Set();

		return width_candidates.reduce((accumulator, width_candidate) => {
			height_candidates.forEach(height_candidate => {
				const [width, height] = normalize_dimension_pair(
					width_candidate.dimension,
					height_candidate.dimension,
				);

				if (!width || !height) {
					return;
				}

				const key = `${width}|${height}`;

				if (seen.has(key)) {
					return;
				}

				seen.add(key);
				accumulator.push({
					label: `${format_dimension(width)} x ${format_dimension(height)} in${width_candidate.is_original && height_candidate.is_original ? ` (${__("Original")})` : ""}`,
					type: "Sheet",
					width,
					height,
				});
			});

			return accumulator;
		}, []);
	}

	function set_derived_dimension_options(options = []) {
		derived_dimension_options = new Map(
			options.map(option => [option.label, option])
		);

		dialog.set_df_property("derived_dimension_choice", "options", [
			"",
			...options.map(option => option.label),
		]);
		dialog.set_value("derived_dimension_choice", "");
		sync_sheet_dimension_field_state();
	}

	function sync_gsm_field_state() {
		const derived_sheet = is_derived_sheet();
		const parent_gsm = to_number(selected_parent_material?.gsm);
		const gsm_read_only = derived_sheet && parent_gsm !== null;
		const gsm_required = !gsm_read_only;

		dialog.set_df_property("gsm", "read_only", gsm_read_only ? 1 : 0);
		dialog.set_df_property("gsm", "reqd", gsm_required ? 1 : 0);
	}

	function sync_sheet_dimension_field_state() {
		const material_format = dialog?.get_value("material_format");
		const derived_sheet = is_derived_sheet();
		const selected_option = derived_dimension_options.get(
			dialog?.get_value("derived_dimension_choice")
		);
		const is_sheet_parent = selected_parent_material?.raw_material_type === "Sheet";
		const is_roll_parent = selected_parent_material?.raw_material_type === "Roll";
		const width_read_only = Boolean(
			derived_sheet && (
				is_sheet_parent
				|| (is_roll_parent && selected_option?.dimension_field === "sheet_width")
			)
		);
		const height_read_only = Boolean(
			derived_sheet && (
				is_sheet_parent
				|| (is_roll_parent && selected_option?.dimension_field === "sheet_height")
			)
		);
		const width_required = material_format === "Sheet" && !derived_sheet && !width_read_only;
		const height_required = material_format === "Sheet" && !derived_sheet && !height_read_only;

		dialog.set_df_property("sheet_width", "read_only", width_read_only ? 1 : 0);
		dialog.set_df_property("sheet_height", "read_only", height_read_only ? 1 : 0);
		dialog.set_df_property("sheet_width", "reqd", width_required ? 1 : 0);
		dialog.set_df_property("sheet_height", "reqd", height_required ? 1 : 0);
	}

	function sync_hidden_standard_sheets(parent_material_sku = "") {
		if (!dialog?.fields_dict?.standard_sheets) {
			return [];
		}

		const rows = parent_material_sku
			? [{ item: parent_material_sku }]
			: [];
		const standard_sheets_field = dialog.fields_dict.standard_sheets;

		standard_sheets_field.df.data = rows;

		if (standard_sheets_field.grid) {
			standard_sheets_field.grid.df.data = rows;
			standard_sheets_field.grid.data = rows;
			standard_sheets_field.grid.refresh();
		}

		dialog.set_value("standard_sheets", rows);

		return rows;
	}

	function clear_derived_sheet_helpers({ clear_parent = false } = {}) {
		selected_parent_material = null;
		set_derived_dimension_options();
		sync_gsm_field_state();
		sync_hidden_standard_sheets();

		if (clear_parent) {
			dialog.set_value("parent_material_sku", "");
		}
	}

	function refresh_derived_sheet_helper_visibility() {
		const derived_sheet = is_derived_sheet();

		dialog.set_df_property("derived_sheet_section", "hidden", !derived_sheet);
		dialog.set_df_property("parent_material_sku", "hidden", !derived_sheet);
		dialog.set_df_property("parent_material_sku", "reqd", derived_sheet);
		dialog.set_df_property("derived_dimension_choice", "hidden", !derived_sheet);
		dialog.set_df_property("derived_dimension_choice", "reqd", derived_sheet);
		dialog.set_df_property("standard_sheets_section", "hidden", 1);
		dialog.set_df_property("standard_sheets", "hidden", 1);
		dialog.set_df_property("standard_sheets", "reqd", 0);

		if (!derived_sheet) {
			clear_derived_sheet_helpers({ clear_parent: true });
			sync_gsm_field_state();
			sync_sheet_dimension_field_state();
			return;
		}

		sync_hidden_standard_sheets(dialog.get_value("parent_material_sku"));
		sync_gsm_field_state();
		sync_sheet_dimension_field_state();
	}

	async function rebuild_derived_dimension_options(parent_material_sku) {
		selected_parent_material = null;
		set_derived_dimension_options();
		sync_hidden_standard_sheets(parent_material_sku);

		if (!parent_material_sku || !is_derived_sheet()) {
			return;
		}

		const requested_parent = parent_material_sku;
		const { message } = await frappe.db.get_value("Item", requested_parent, [
			"gsm",
			"raw_material_type",
			"roll_width",
			"sheet_width",
			"sheet_height",
		]);

		if (dialog.get_value("parent_material_sku") !== requested_parent) {
			return;
		}

		selected_parent_material = message || null;

		const options = selected_parent_material?.raw_material_type === "Roll"
			? build_roll_parent_options(selected_parent_material)
			: build_sheet_parent_options(selected_parent_material || {})
		;

		if (to_number(selected_parent_material?.gsm) !== null) {
			dialog.set_value("gsm", selected_parent_material.gsm);
		}

		set_derived_dimension_options(options);
		sync_gsm_field_state();
		sync_sheet_dimension_field_state();

		if (!options.length) {
			frappe.show_alert({
				message: __("No valid derived dimensions were found for the selected parent SKU."),
				indicator: "orange",
			});
		}
	}

	function apply_selected_sheet_option(option_label) {
		const option = derived_dimension_options.get(option_label);

		if (!option || option.type !== "Sheet") {
			sync_sheet_dimension_field_state();
			return;
		}

		dialog.set_value("sheet_width", option.width);
		dialog.set_value("sheet_height", option.height);
		sync_sheet_dimension_field_state();
	}

	function validate_derived_sheet_selection(values) {
		if (!is_derived_sheet(values)) {
			values.standard_sheets = [];
			return;
		}

		if (!values.parent_material_sku) {
			frappe.throw(__("Please select a parent material SKU."));
		}

		if (!values.derived_dimension_choice) {
			frappe.throw(__("Please select a derived dimension option."));
		}

		const selected_option = derived_dimension_options.get(values.derived_dimension_choice);

		if (!selected_option) {
			frappe.throw(__("Please select a valid derived dimension option."));
		}

		const sheet_width = normalize_dimension(values.sheet_width);
		const sheet_height = normalize_dimension(values.sheet_height);
		const entered_gsm = to_number(values.gsm);
		const parent_gsm = to_number(selected_parent_material?.gsm);

		if (sheet_width === null || sheet_height === null) {
			frappe.throw(__("Please enter both sheet width and sheet height."));
		}

		if (parent_gsm !== null && entered_gsm !== parent_gsm) {
			frappe.throw(__("GSM must match the selected parent SKU."));
		}

		if (selected_option.type === "Roll") {
			const matches_roll_side = dimensions_match(sheet_width, selected_option.side)
				|| dimensions_match(sheet_height, selected_option.side)
			;

			if (!matches_roll_side) {
				frappe.throw(__("One sheet side must match the selected roll-width proportion."));
			}
		}

		if (selected_option.type === "Sheet") {
			const [entered_width, entered_height] = normalize_dimension_pair(sheet_width, sheet_height);
			const [selected_width, selected_height] = normalize_dimension_pair(
				selected_option.width,
				selected_option.height,
			);

			if (
				!dimensions_match(entered_width, selected_width)
				|| !dimensions_match(entered_height, selected_height)
			) {
				frappe.throw(__("The sheet dimensions must match the selected parent-sheet option."));
			}
		}

		values.standard_sheets = sync_hidden_standard_sheets(values.parent_material_sku);
	}

	function _render_dialog(form) {
		dialog = new frappe.ui.Dialog({
			title: __("Crear un nuevo SKU"),
			size: "extra-large", // Makes the dialog wider
			fields: [
				{
					fieldtype: "HTML",
					fieldname: "material_description",
					options: `<p class="text-muted">Material</p>
				<h3>${form.description}</h3>`,
				},
				{
					fieldtype: "Section Break",
					label: __("Especificación del Material"),
				},
				{
					fieldname: "material_format",
					fieldtype: "Select",
					label: __("Formato del Material"),
					reqd: 1,
					default: "Roll",
					options: [
						"Roll",
						"Sheet",
					],
					change(event) {
						const material_format = event?.target?.value || dialog.get_value("material_format");

						dialog.set_df_property("roll_width", "reqd", material_format === "Roll");
						dialog.set_df_property("roll_width", "hidden", material_format === "Sheet");
						dialog.set_df_property("sheet_width", "reqd", material_format === "Sheet");
						dialog.set_df_property("sheet_width", "hidden", material_format === "Roll");
						dialog.set_df_property("sheet_height", "reqd", material_format === "Sheet");
						dialog.set_df_property("sheet_height", "hidden", material_format === "Roll");
						dialog.set_df_property("standard_sheet_size", "hidden", material_format === "Roll");
						dialog.set_df_property("standard_sheet_size", "reqd", material_format === "Sheet");

						if (material_format !== "Sheet") {
							dialog.set_value("standard_sheet_size", "");
						}

						refresh_derived_sheet_helper_visibility();
					}
				},
				{
					fieldname: "standard_sheet_size",
					fieldtype: "Select",
					label: __("Tamaño de Hoja Estándar"),
					// hidden: 1,
					reqd: 0,
					default: "",
					options: [
						"",
						"Estándar",
						"Derivado",
					],
					change(event) {
						const standard_sheet_size = event?.target?.value || dialog.get_value("standard_sheet_size");

						if (standard_sheet_size !== "Derivado") {
							clear_derived_sheet_helpers({ clear_parent: true });
						}

						refresh_derived_sheet_helper_visibility();
					}
				},
				{ fieldtype: "Column Break" },
				{
					fieldname: "roll_width",
					fieldtype: "Float",
					label: `${__("Ancho del Rollo")} (in)`,
					reqd: 1,
					precision: 3,
					async change(event) {
						const { target } = event;
						await frappe.timeout(.1);

						const value = round_to_nearest_eighth(target.value);
						if (target.value !== value) {
							target.value = value;
						}
					},
				},
				{
					fieldname: "sheet_width",
					fieldtype: "Float",
					label: `${__("Ancho de la Hoja")} (in)`,
					hidden: 1,
					precision: 3,
					async change(event) {
						const { target } = event;
						await frappe.timeout(.1);

						const value = round_to_nearest_eighth(target.value);
						if (target.value !== value) {
							target.value = value;
						}
					},
				},
				{
					fieldname: "sheet_height",
					fieldtype: "Float",
					label: `${__("Alto de la Hoja")} (in)`,
					hidden: 1,
					precision: 3,
					async change(event) {
						const { target } = event;
						await frappe.timeout(.1);

						const value = round_to_nearest_eighth(target.value);
						if (target.value !== value) {
							target.value = value;
						}
					},
				},
				{
					fieldtype: "Section Break",
					fieldname: "derived_sheet_section",
					label: __("Hoja Derivada"),
					hidden: 1,
				},
				{
					fieldname: "parent_material_sku",
					fieldtype: "Link",
					label: __("SKU Padre del Material"),
					options: "Item",
					hidden: 1,
					get_query() {
						return {
							filters: {
								is_raw_material: 1,
								reference_type: "Raw Material",
								reference_name: docname,
								raw_material_type: ["in", ["Roll", "Sheet"]],
							},
						};
					},
					async change() {
						const parent_material_sku = dialog.get_value("parent_material_sku");

						if (!parent_material_sku) {
							clear_derived_sheet_helpers();
							return;
						}

						await rebuild_derived_dimension_options(parent_material_sku);
					},
				},
				{
					fieldtype: "Column Break",
				},
				{
					fieldname: "derived_dimension_choice",
					fieldtype: "Select",
					label: __("Dimensión Derivada"),
					options: [""],
					hidden: 1,
					change() {
						apply_selected_sheet_option(dialog.get_value("derived_dimension_choice"));
					},
				},
				{
					fieldtype: "Section Break",
					label: __("Peso"),
				},
				{
					fieldname: "gsm",
					fieldtype: "Int",
					non_negative: 1,
					reqd: 1,
					label: __("GSM"),
					async change(event) {
						const { target } = event;
						await frappe.timeout(.1);

						if (!target.value) {
							target.value = 0;
						}

						if (
							target.value < 0
						) {
							target.value = 0;

							frappe.show_alert({
								message: __("GSM cannot be negative!"),
								indicator: "red",
							});
						}
					},
				},
				{ fieldtype: "Section Break", fieldname:  "standard_sheets_section" },
				{
					fieldname: "standard_sheets",
					fieldtype: "Table",
					label: __("Hojas Estándar"),
					reqd: 0,
					cannot_add_rows: 0,
					in_place_edit: true,
					data: [],
					get_data: () => {
						return dialog?.fields_dict?.standard_sheets?.df?.data || [];
					},
					fields: [
						{
							fieldname: 'item',
							fieldtype: 'Link',
							options: 'Item',
							label: __('Artículo'),
							in_list_view: 1,
							reqd: 1,
							get_query(doc) {
								const gsm = dialog.get_value("gsm");
								const standard_sheets = dialog.get_value("standard_sheets") || [];

								return {
									filters: {
										"reference_name": docname,
										"is_standard_sheet_size": 1,
										"raw_material_type": "Sheet",
										"gsm": gsm,
										"name": [
											"not in", 
											standard_sheets
												.filter(row => row.name !== doc.name)
												.map(row => row.item)

										],
									}
								}
							},
							onchange() {
								const { grid_row } = this;

								const { description } = grid_row.on_grid_fields_dict;

								const { value } = this;

								if (value) {
									frappe.db.get_value("Item", value, ["description"])
										.then(({ message }) => {
											if (message.description) {
												description.set_value(message.description);
											}
										});
								}
							},
						},
							{
								fieldname: 'description',
								fieldtype: 'Small Text',
								label: __('Descripción'),
								in_list_view: 1,
							}
						],
					},
					{
						fieldtype: "Section Break",
						label: __("Grupo de Artículos"),
						fieldname: "item_groups_section",
					},
					{
						fieldname: "item_group_1",
						fieldtype: "Link",
						label: __("Grupo de Artículos 1"),
					options: "Item Group",
					default: form.item_group_1 || frappe.boot?.powerpro_settings?.root_item_group_for_raw_materials,
					read_only: Boolean(frappe.boot?.powerpro_settings?.root_item_group_for_raw_materials),
					// reqd: 0,
					change(event) {},
				},
					{
						fieldname: "item_group_2",
						fieldtype: "Link",
						label: __("Grupo de Artículos 2"),
					options: "Item Group",
					default: form.item_group_2,
					// reqd: 0,
					get_query() {
						return {
							filters: {
								parent_item_group: dialog.get_value("item_group_1"),
							},
						};
					},
					change(event) {
						// toggle visibility of the next field based on the value of this field
						// and if it's a group or not
						const { value } = this;

						if (value) {
							// const item_group = item_group_details.find(item_group => item_group.name === value);
							// const is_group = item_group?.is_group;
							const has_children = item_group_details.find(item_group => item_group.parent_item_group === value);

							dialog.set_df_property("item_group_3", "hidden", !has_children);
							// dialog.set_df_property("item_group_3", "reqd", has_children);
						} else {
							dialog.set_df_property("item_group_5", "hidden", 1);
							// dialog.set_df_property("item_group_3", "reqd", 0);
						}

						dialog.set_value("item_group_3", null);
					},
				},
					{
						fieldname: "item_group_3",
						fieldtype: "Link",
						label: __("Grupo de Artículos 3"),
					options: "Item Group",
					default: form.item_group_3,
					hidden: !Boolean(form.item_group_3),
					get_query() {
						return {
							filters: {
								parent_item_group: dialog.get_value("item_group_2"),
							},
						};
					},
					change(event) {
						// toggle visibility of the next field based on the value of this field
						// and if it's a group or not
						const { value } = this;

						if (value) {
							// const item_group = item_group_details.find(item_group => item_group.name === value);
							// const is_group = item_group?.is_group;
							const has_children = item_group_details.find(item_group => item_group.parent_item_group === value);

							dialog.set_df_property("item_group_4", "hidden", !has_children);
							// dialog.set_df_property("item_group_4", "reqd", has_children);
						} else {
							dialog.set_df_property("item_group_4", "hidden", 1);
							// dialog.set_df_property("item_group_4", "reqd", 0);
						}
										
						dialog.set_value("item_group_4", null);
					},
				},
					{
						fieldname: "item_group_4",
						fieldtype: "Link",
						label: __("Grupo de Artículos 4"),
					options: "Item Group",
					default: form.item_group_4,
					hidden: !Boolean(form.item_group_4),
					get_query() {
						return {
							filters: {
								parent_item_group: dialog.get_value("item_group_3"),
							},
						};
					},
					change(event) {
						// toggle visibility of the next field based on the value of this field
						// and if it's a group or not
						const { value } = this;

						if (value) {
							// const item_group = item_group_details.find(item_group => item_group.name === value);
							// const is_group = item_group?.is_group;
							const has_children = item_group_details.find(item_group => item_group.parent_item_group === value);

							dialog.set_df_property("item_group_5", "hidden", !has_children);
							// dialog.set_df_property("item_group_5", "reqd", has_children);
						} else {
							dialog.set_df_property("item_group_5", "hidden", 1);
							// dialog.set_df_property("item_group_5", "reqd", 0);
						}
										
						dialog.set_value("item_group_5", null);
					},
				},
					{
						fieldname: "item_group_5",
						fieldtype: "Link",
						label: __("Grupo de Artículos 5"),
					options: "Item Group",
					default: form.item_group_5,
					hidden: !Boolean(form.item_group_5),
					get_query() {
						return {
							filters: {
								parent_item_group: dialog.get_value("item_group_4"),
							},
						};
					},
					change(event) {},
				},
			],
			primary_action_label: __("Crear SKU"),
			primary_action(values) {
				validate_derived_sheet_selection(values);

				const payload = {
					...values,
					standard_sheet_size: values.standard_sheet_size === "Estándar"
						? "Standard"
						: values.standard_sheet_size,
				};

				frappe.call("powerpro.manufacturing_pro.doctype.raw_material.client.create_material_sku", {
					material_id: docname,
					...payload,
				}).then(function(response) {
					const { message } = response;

					if (message) {
						dialog.hide();
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
			}
		});

		dialog.set_df_property("standard_sheet_size", "hidden", 1); // select field [Standard, Derivado]
		dialog.set_df_property("standard_sheets_section", "hidden", 1); // section break before the table
		dialog.set_df_property("standard_sheets", "hidden", 1); // table
		dialog.set_df_property("derived_sheet_section", "hidden", 1);
		dialog.set_df_property("parent_material_sku", "hidden", 1);
		dialog.set_df_property("derived_dimension_choice", "hidden", 1);
		dialog.set_df_property("item_groups_section", "hidden", 1); // table
		sync_gsm_field_state();
		refresh_derived_sheet_helper_visibility();
		
		// Show the dialog
		dialog.show();
	}
}
