// Source Client Script: Mostrar Barra Selección de Tinta en Generador de Producto
// Site: igcaribe.fortabs.com

frappe.ui.form.on('Product Generator', {
    refresh(frm) {
        if (!frm.doc.requiere_impresion) {
            ['tiro', 'retiro'].forEach(tipo => {
                frm.fields_dict[`html_tinta_${tipo}`]?.$wrapper.empty().hide();
                frm.fields_dict[`html_cargar_cuatricomia_${tipo}`]?.$wrapper.empty().hide();
            });
            return;
        }

        ['tiro', 'retiro'].forEach(tipo => {
            frm.fields_dict[`html_tinta_${tipo}`]?.$wrapper.show();
            frm.fields_dict[`html_cargar_cuatricomia_${tipo}`]?.$wrapper.show();
        });

        render_tintas(frm);
    },

    requiere_impresion(frm) {
        if (!frm.doc.requiere_impresion) {
            ['cantidad_tinta_tiro', 'cantidad_tinta_retiro'].forEach(campo => {
                if (frm.doc[campo]) frm.set_value(campo, null);
            });

            ['tiro', 'retiro'].forEach(tipo => {
                for (let i = 1; i <= 8; i++) {
                    const campo = `tinta_${tipo}_${i}`;
                    const campo_color = `${campo}_color`;
                    if (frm.doc[campo]) frm.set_value(campo, null);
                    if (frm.doc[campo_color]) frm.set_value(campo_color, null);
                }
            });
        }

        frm.refresh();
    },

    cantidad_tinta_tiro(frm) {
        render_tintas(frm);
    },

    cantidad_tinta_retiro(frm) {
        render_tintas(frm);
    },

    tiro(frm) {
        if (!frm.doc.tiro) frm.set_value('cantidad_tinta_tiro', null);
        render_tintas(frm);
    },

    retiro(frm) {
        if (!frm.doc.retiro) frm.set_value('cantidad_tinta_retiro', null);
        render_tintas(frm);
    },

    validate(frm) {
        const errores = [];

        ['tiro', 'retiro'].forEach(tipo => {
            const cantidad = cint(frm.doc[`cantidad_tinta_${tipo}`]);
            for (let i = 1; i <= 8; i++) {
                const campo = `tinta_${tipo}_${i}`;
                const campo_color = `${campo}_color`;

                if (i <= cantidad) {
                    if (!frm.doc[campo]) errores.push(`Debe seleccionar la tinta ${i} de ${tipo}.`);
                } else {
                    frm.doc[campo] = null;
                    frm.doc[campo_color] = null;
                }
            }
        });

        if (errores.length) frappe.throw(errores.join('<br>'));
    }
});

function render_tintas(frm) {
    ['tiro', 'retiro'].forEach(tipo => render_barras(frm, tipo));
    mostrar_boton_cuatricomia(frm);  // <- Aquí se llama siempre después de renderizar
}

function render_barras(frm, tipo) {
    const cantidad = cint(frm.doc[`cantidad_tinta_${tipo}`] || 0);
    const contenedor = frm.fields_dict[`html_tinta_${tipo}`]?.$wrapper;
    if (!contenedor) return;

    contenedor.empty();
    if (!cantidad) return;

    for (let i = 1; i <= cantidad; i++) {
        const campo = `tinta_${tipo}_${i}`;
        const campo_color = `${campo}_color`;
        const nombre_color = frm.doc[campo] || '';

        if (!nombre_color) continue;

        // Si ya tenemos el hex, úsalo directamente
        let color_hex = frm.doc[campo_color];

        const crear_barra = (hex) => {
            const barra = $(`
                <div style="display:flex;height:30px;border-radius:8px;overflow:hidden;margin:10px 0;">
                    <div style="flex:0 0 20%;background:${hex};display:flex;align-items:center;justify-content:center;color:#fff;font-weight:bold;">
                        &nbsp;
                    </div>
                    <div style="flex:0 0 60%;background:#f4f4f4;display:flex;align-items:center;padding-left:8px;font-size:13px;">
                        ${nombre_color}
                    </div>
                    <div class="barra-boton" style="flex:0 0 20%;background:#000;color:#fff;display:flex;align-items:center;justify-content:center;cursor:pointer;">
                        <i class="fa fa-crosshairs"></i>
                    </div>
                </div>
            `);

            barra.find('.barra-boton').on('click', () => {
                abrir_selector_tinta(frm, tipo, i, campo, campo_color);
            });

            contenedor.append(barra);
        };

        // Si no hay color_hex, busca desde el Doctype Ink Color
        if (!color_hex) {
            frappe.db.get_doc('Ink Color', nombre_color).then(doc => {
                color_hex = doc.hexadecimal_color || '#ccc';
                frm.set_value(campo_color, color_hex); // opcional para persistencia
                crear_barra(color_hex);
            });
        } else {
            crear_barra(color_hex);
        }
    }
}


function abrir_selector_tinta(frm, tipo, index, campo, campo_color) {
    const dialog = new frappe.ui.Dialog({
        title: `Seleccionar Tinta ${index} (${tipo})`,
        fields: [
            {
                fieldname: 'ink_color',
                label: 'Color',
                fieldtype: 'Link',
                options: 'Ink Color',
                reqd: 1,
                get_query: () => {
                    const cantidad = cint(frm.doc[`cantidad_tinta_${tipo}`] || 0);
                    const seleccionadas = [];
                    for (let i = 1; i <= cantidad; i++) {
                        const campo_tmp = `tinta_${tipo}_${i}`;
                        if (frm.doc[campo_tmp] && campo_tmp !== campo) {
                            seleccionadas.push(frm.doc[campo_tmp]);
                        }
                    }
                    return { filters: [['name', 'not in', seleccionadas]] };
                }
            }
        ],
        primary_action_label: 'Seleccionar',
        primary_action(values) {
            frappe.db.get_doc('Ink Color', values.ink_color).then(doc => {
                frm.set_value(campo, doc.name);
                frm.set_value(campo_color, doc.hexadecimal_color || '#ccc');
                render_barras(frm, tipo);
                dialog.hide();
            });
        }
    });

    dialog.show();
}

function mostrar_boton_cuatricomia(frm) {
    ['tiro', 'retiro'].forEach(tipo => {
        const cantidad = cint(frm.doc[`cantidad_tinta_${tipo}`] || 0);
        const wrapper = frm.fields_dict[`html_cargar_cuatricomia_${tipo}`]?.$wrapper;
        if (!wrapper) return;

        wrapper.empty();

        if (cantidad >= 4) {
            const boton = $(`<button class="btn btn-sm btn-primary">
                <i class="fa fa-palette"></i> Cargar Cuatricromía
            </button>`);

            boton.on('click', () => cargar_cuatricromia(frm, tipo));
            wrapper.append(boton);
        }
    });
}

function cargar_cuatricromia(frm, tipo) {
    frappe.db.get_doc('Power-Pro Settings', 'Power-Pro Settings').then(config => {
        const nombres = [
            config.cyan_color, config.magenta_color,
            config.yellow_color, config.key_color
        ];

        if (nombres.some(n => !n)) {
            frappe.msgprint('Faltan colores configurados en Power-Pro Settings.');
            return;
        }

        nombres.forEach((color_name, i) => {
            const idx = i + 1;
            const campo = `tinta_${tipo}_${idx}`;
            const campo_color = `${campo}_color`;

            frappe.db.get_doc('Ink Color', color_name).then(doc => {
                frm.set_value(campo, doc.name);
                frm.set_value(campo_color, doc.hexadecimal_color || '#ccc');
                render_barras(frm, tipo);
            });
        });
    });
}

function cint(val) {
    return parseInt(val || '0');
}
