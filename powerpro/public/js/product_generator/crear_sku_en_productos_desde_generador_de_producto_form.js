frappe.ui.form.on('Product Generator', {
    async refresh(frm) {
        frm.set_df_property('tipo_producto', 'read_only', frm.doc.docstatus === 1 || frm.doc.__is_draft_from_edit);
        frm.clear_custom_buttons();
        if (frm.is_new()) return;

        // Obtener hash actual del documento
        const normalize = get_normalizer();
        const specs_data = get_normalized_specs(frm.doc, normalize);
        let custom_group_1 = '', custom_group_2 = '';

        if (frm.doc.tipo_producto) {
            try {
                const product_type = await frappe.db.get_doc('Product Type', frm.doc.tipo_producto);
                custom_group_1 = normalize(product_type.item_group_1 || '');
                custom_group_2 = normalize(product_type.item_group_2 || '');
                specs_data.push(custom_group_1, custom_group_2);
            } catch (e) {
                frappe.msgprint("No se pudo obtener Product Type.");
                return;
            }
        }

        const r = await frappe.call({
            method: "get_product_hash",
            args: { docname: frm.doc.name }
        });

        const hash = r.message.product_hash;


        if (frm.doc.docstatus === 0 && frm.doc.product_hash !== hash) {
            frm.doc.product_hash = hash;
            frm.refresh_field("product_hash");
        }

        // Revisar si hay un ítem existente con el mismo hash
        frm._item_asociado = frm.doc.item_asociado || null;

        const existing_item = await frappe.db.get_list('Item', {
            filters: {
                reference_type: frm.doctype,
                reference_name: frm.docname
            },
            fields: ['name', 'product_generator'],
            limit: 1
        });

        frm.dashboard.clear_headline();
        let es_mi_item = false;

        if (existing_item.length > 0) {
            const item = existing_item[0];
            es_mi_item = (item.product_generator || "").trim() === frm.doc.name.trim();

            if (es_mi_item || item.name === frm.doc.item_asociado) {
                frm._item_asociado = item.name;
                if (frm.doc.item_asociado !== item.name) {
                    frm.doc.item_asociado = item.name;
                    frm.refresh_field("item_asociado");
                }
            }

            frm.dashboard.set_headline(`
                <div>
                    <span style="color:red; font-weight:bold;">Ya existe un SKU con estas mismas especificaciones.</span><br>
                    <button class="btn btn-info btn-xs" style="margin: 6px 0;" onclick="frappe.utils.copy_to_clipboard('${item.name}')">
                        Copiar SKU
                    </button>
                    <a href="/app/item/${item.name}" target="_blank">Ir al Ítem: <b>${item.name}</b></a>
                </div>
            `);
        }

        if (es_mi_item && frm.doc.docstatus === 1) {
            const autorizado = await verificar_permiso_usuario(frappe.session.user);
            if (autorizado) {
                frm.add_custom_button("Habilitar Edición", async () => {
                    frappe.confirm("¿Enviar este registro a Borrador para editar?", async () => {
                        await frappe.call({
                            method: "igcaribe.client.set_back_to_draft",
                            args: { doctype: frm.doctype, name: frm.docname },
                            callback: async () => {
                                frappe.show_alert("Documento en modo Borrador", 4);
                                frm.doc.__is_draft_from_edit = true;
                                await frm.reload_doc();
                                desbloquear_campos(frm);
                                setTimeout(() => {
                                    frm.set_df_property('tipo_producto', 'read_only', 1);
                                    if (frm.get_field('tipo_producto').$input) {
                                        frm.get_field('tipo_producto').$input.prop('disabled', true);
                                    }
                                }, 100);
                            }
                        });
                    });
                }).addClass('btn-primary');
            }
        }

        // !frm._item_asociado &&
        //  && existing_item.length === 0
        if (frm.doc.docstatus === 1) {
            const ya_existe = await frappe.db.get_list('Item', {
                filters: { reference_type: frm.doctype, reference_name: frm.docname },
                limit: 1
            });
               
            const doc_args = {
                doctype: 'Item',
                item_type: 'Bienes',
                stock_uom: 'ud(s)',
                custom_item_group_1: custom_group_1,
                custom_item_group_2: custom_group_2,
                item_name: frm.doc.item_name,
                description: frm.doc.description,
                product_generator: frm.doc.name,
                product_hash: frm.doc.product_hash,
                ...Object.fromEntries(get_fields_to_compare().map(f => [f, frm.doc[f]])),
                reference_type: frm.doctype,
                reference_name: frm.doc.name,
            };
            sanitize_item_ink_slots(doc_args);
            const autorizado = await verificar_permiso_usuario(frappe.session.user);
                 if (autorizado) {
            if (ya_existe.length > 0) {
                frm.add_custom_button("Actualizar SKU", async () => {
                    frappe.call({
                        method: 'frappe.client.set_value',
                        args: {
                            doctype: 'Item',
                            name: ya_existe[0].name,
                            fieldname: doc_args
                        },
                        callback: (r) => {
                            if (!r.exc) {
                                frappe.msgprint(`SKU actualizado: <a href="/app/item/${ya_existe[0].name}" target="_blank">${ya_existe[0].name}</a>`);
                                frm._item_asociado = ya_existe[0].name;
                                frm.set_value("item_asociado", ya_existe[0].name);
                                frm.reload_doc();
                            }
                        }
                    });
                }).addClass('btn-primary');
            } else {
                frm.add_custom_button("Crear SKU", async () => {
                    frappe.call({
                        method: 'frappe.client.insert',
                        args: { doc: doc_args },
                        callback: (r) => {
                            if (!r.exc) {
                                frappe.msgprint(`SKU creado: <a href="/app/item/${r.message.name}" target="_blank">${r.message.name}</a>`);
                                frm._item_asociado = r.message.name;
                                frm.set_value("item_asociado", r.message.name);
                                frm.reload_doc();
                            }
                        }
                    });
                });
            }
        }
        }
    }, // end of refresh
});

// ---------------- FUNCIONES AUXILIARES ----------------

function get_fields_to_compare() {
    return [
        'own_made', 'tipo_producto', 'material',
        'ancho_producto', 'alto_producto',
        'requiere_impresion', 'tiro', 'retiro',
        'requiere_laminado', 'requiere_barnizado', 'requiere_acabado_especial',
        'requiere_troquelado', 'requiere_cinta_doble_cara', 'requiere_pegado',
        'cantidad_tinta_tiro', 'cantidad_tinta_retiro',
        'tipo_de_laminado', 'tipo_de_barnizado', 'tipo_de_pegado',
        'acabado_especial', 'elementos_acabado_especial', 'foil_color',
        'ancho_elemento_1', 'alto_elemento_1',
        'ancho_elemento_2', 'alto_elemento_2',
        'ancho_elemento_3', 'alto_elemento_3',
        'ancho_elemento_4', 'alto_elemento_4',
        'ancho_elemento_5', 'alto_elemento_5',
        'ancho_elemento_6', 'alto_elemento_6',
        'puntos_cinta_doble_cara', 'ancho_punto_cinta_doble_cara', 'alto_punto_cinta_doble_cara',
        'tinta_tiro_1', 'tinta_tiro_2', 'tinta_tiro_3', 'tinta_tiro_4',
        'tinta_tiro_5', 'tinta_tiro_6', 'tinta_tiro_7', 'tinta_tiro_8',
        'tinta_retiro_1', 'tinta_retiro_2', 'tinta_retiro_3', 'tinta_retiro_4',
        'tinta_retiro_5', 'tinta_retiro_6', 'tinta_retiro_7', 'tinta_retiro_8'
    ];
}

function get_normalizer() {
    return function (value) {
        if (value === null || value === undefined || value === '') return '';
        if (typeof value === 'boolean') return value ? '1' : '0';
        if (typeof value === 'number') return value.toFixed(4);
        return String(value).trim().toLowerCase();
    };
}

function get_normalized_specs(doc, normalize) {
    const data = [];
    const pairs_to_sort = [
        ['ancho_producto', 'alto_producto'],
        ['ancho_punto_cinta_doble_cara', 'alto_punto_cinta_doble_cara'],
        ['ancho_elemento_1', 'alto_elemento_1'],
        ['ancho_elemento_2', 'alto_elemento_2'],
        ['ancho_elemento_3', 'alto_elemento_3'],
        ['ancho_elemento_4', 'alto_elemento_4'],
        ['ancho_elemento_5', 'alto_elemento_5'],
        ['ancho_elemento_6', 'alto_elemento_6']
    ];
    const excluded_fields = [...pairs_to_sort.flat(), ...Array.from({ length: 8 }, (_, i) => `tinta_tiro_${i + 1}`), ...Array.from({ length: 8 }, (_, i) => `tinta_retiro_${i + 1}`)];

    get_fields_to_compare().forEach(f => {
        if (!excluded_fields.includes(f)) {
            data.push(normalize(doc[f]));
        }
    });

    for (const [f1, f2] of pairs_to_sort) {
        data.push(...[normalize(doc[f1]), normalize(doc[f2])].sort());
    }

    const tintas_tiro = Array.from({ length: 8 }, (_, i) => normalize(doc[`tinta_tiro_${i + 1}`] || '')).filter(Boolean).sort();
    const tintas_retiro = Array.from({ length: 8 }, (_, i) => normalize(doc[`tinta_retiro_${i + 1}`] || '')).filter(Boolean).sort();
    data.push(...tintas_tiro, ...tintas_retiro);

    return data;
}

async function calcular_hash(data_array) {
    const encoder = new TextEncoder();
    const hashBuffer = await crypto.subtle.digest("SHA-256", encoder.encode(data_array.join("|")));
    return Array.from(new Uint8Array(hashBuffer)).map(b => b.toString(16).padStart(2, '0')).join("");
}

async function verificar_permiso_usuario(user) {
    const settings = await frappe.db.get_doc('Product Generator Settings');
    return settings.allowed_modify_users?.map(r => r.users).includes(user);
}

function desbloquear_campos(frm) {
    frm.fields.forEach(df => {
        if (df.df && df.df.fieldname !== 'tipo_producto') {
            frm.set_df_property(df.df.fieldname, 'read_only', 0);
        }
    });
    frm.enable_save();
}

function sanitize_item_ink_slots(doc) {
    ['tiro', 'retiro'].forEach(tipo => {
        const cantidad = parseInt(doc[`cantidad_tinta_${tipo}`] || 0, 10) || 0;
        for (let i = 1; i <= 8; i++) {
            if (i > cantidad) {
                doc[`tinta_${tipo}_${i}`] = null;
            }
        }
    });
}
