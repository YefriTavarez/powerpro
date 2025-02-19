// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt

{
    // const assets = new Object();
    
    function set_udm_queries(frm, data) {
        const {
            fields_with_categories,
            uoms_by_category
        } = data;

        for (const fieldname in fields_with_categories) {
            const uom_category = fields_with_categories[fieldname];
            
            if (!uom_category) {
                frm.set_query(fieldname, function() {
                    return { filters: { name: "None" }};
                })
                
                continue
            }
            
            const uom_list = uoms_by_category[uom_category];
            
            if (!uom_list.length) {
                uom_list.push("N/A");
            }
            
            frm.set_query(fieldname, function() {
                const filters = {
                    name: ["in", uom_list],
                };
                
                return { filters };
            });
        }
    }
    
    function fetch_uom_categories(frm) {
        const { doc } = frm;
        
        frappe.call({
        	method: "igcaribe.client.get_uom_categories",
        	args: {
        		"item_name_id": doc.item
        	},
        	callback: function({ message: data }) {
        	    set_udm_queries(frm, data);
        	},
        });
    }

    frappe.ui.form.on('Item Generator', {
        refresh: function(frm) {
            if (frm.doc.docstatus !== 1) {
                return ; // only aplicable for submitted documents
            }


            const { doc } = frm;

            const { __onload: onload } = doc;
            if (onload && !onload.item_exists) {
                frm.add_custom_button("Crear SKU", function() {
                    if (frm.doc.__unsaved) {
                        frappe.throw("Favor de guardar el documento antes de intentar crear el SKU");
                    }

                    const method = "igcaribe.client.create_sku_based_on_item_generator";
                    const args = {
                        item_generator_id: frm.doc.name,
                    };
                    
                    function callback({ message }) {
                        frappe.prompt([
                            {fieldtype: "HTML", options: 
                                                `El SKU ${message} ha sido creado satisfactoriamente.<br>
                                                <button class="btn btn-info" onclick="frappe.utils.copy_to_clipboard('${message}')">Copiar al Porta Papeles</button>
                                                `}], function() {
                            frappe.set_route(`/app/item/${message}`);
                            }, "SKU Creado", "Ver SKU");
                    
                    }

                    frappe.call({ method, args, callback });
                });
            }
        },
        before_load: function(frm) {
            frm.trigger("setup_fields");
        },
        onload: function (frm) {
            frm.trigger("setup_queries");
        },
        toggle_display_data_fields: function (frm) {
            // Ocultar todos los campos excepto "item" y los breaks por defecto
            frm.fields.forEach(field => {
                if (
                    field.df.fieldtype === "Column Break"
                    || field.df.fieldtype === "Section Break"
                    || field.df.fieldtype === "Tab Break"
                    || field.df.fieldname === "item"
                    || field.df.fieldname === "description"
                ) {
                    frm.set_df_property(field.df.fieldname, "hidden", false); // Siempre visible
                } else {
                    frm.set_df_property(field.df.fieldname, "hidden", true); // Ocultar por defecto
                }
            });
    
            frm.refresh(); // Aplicar cambios iniciales
        },
    
        item: function (frm) {
            frm.trigger("setup_fields");
        },
    
        setup_queries: function (frm) {
            // frm.set_query("conectividad", function() {
            //     const query = "powerpro.controllers.queries.item_connectivity.get_item_connectivity";
            //     const filters = {
            //         item_name: frm.doc.item,
            //     };
            
            //     return { filters, query };
            // });

            frm.set_query("spec1", function() {
                const query = "powerpro.controllers.queries.get_item_specs_1";
                const filters = {
                    item_name: frm.doc.item,
                };
                return { filters, query };
            });

            frm.set_query("spec2", function() {
                const query = "powerpro.controllers.queries.get_item_specs_2";
                const filters = {
                    item_name: frm.doc.item,
                };
                return { filters, query };
            });

            frm.set_query("use", function() {
                const query = "powerpro.controllers.queries.get_item_use";
                const filters = {
                    item_name: frm.doc.item,
                };
                return { filters, query };
            });

            frm.set_query("packaging", function() {
                const query = "powerpro.controllers.queries.get_item_packaging";
                const filters = {
                    item_name: frm.doc.item,
                };
                return { filters, query };
            });

            frm.set_query("size", function() {
                const query = "powerpro.controllers.queries.get_item_size";
                const filters = {
                    item_name: frm.doc.item,
                };
                return { filters, query };
            });

            // frm.set_query("presentation_uom", function() {
            //     const query = "powerpro.controllers.queries.get_uom";
            //     const filters = {
            //         item_name: frm.doc.item,
            //     };
            //     return { filters, query };
            // });

            frm.set_query("material", function() {
                const query = "powerpro.controllers.queries.get_item_material";
                const filters = {
                    item_name: frm.doc.item,
                };
                return { filters, query };
            });

            frm.set_query("color", function() {
                const query = "powerpro.controllers.queries.get_item_color";
                const filters = {
                    item_name: frm.doc.item,
                };
                return { filters, query };
            });

            frm.set_query("finish", function() {
                const query = "powerpro.controllers.queries.get_item_finish";
                const filters = {
                    item_name: frm.doc.item,
                };
                return { filters, query };
            });

            frm.set_query("flavour", function() {
                const query = "powerpro.controllers.queries.get_item_flavour";
                const filters = {
                    item_name: frm.doc.item,
                };
                return { filters, query };
            });

            frm.set_query("brand", function() {
                const query = "powerpro.controllers.queries.get_item_brand";
                const filters = {
                    item_name: frm.doc.item,
                };
                return { filters, query };
            });

            frm.set_query("model", function() {
                const query = "powerpro.controllers.queries.get_item_model";
                const filters = {
                    item_name: frm.doc.item,
                    item_brand: frm.doc.brand || "N/A",
                };
                return { filters, query };
            });

            frm.set_query("shape", function() {
                const query = "powerpro.controllers.queries.get_item_shape";
                const filters = {
                    item_name: frm.doc.item,
                };
                return { filters, query };
            });

            // frm.set_query("gauge_uom", function() {
            //     const query = "powerpro.controllers.queries.get_uom";
            //     const filters = {
            //         item_name: frm.doc.item,
            //     };
            //     return { filters, query };
            // });

            // frm.set_query("width_uom", function() {
            //     const query = "powerpro.controllers.queries.get_uom";
            //     const filters = {
            //         item_name: frm.doc.item,
            //     };
            //     return { filters, query };
            // });

            // frm.set_query("height_uom", function() {
            //     const query = "powerpro.controllers.queries.get_uom";
            //     const filters = {
            //         item_name: frm.doc.item,
            //     };
            //     return { filters, query };
            // });

            // frm.set_query("depth_uom", function() {
            //     const query = "powerpro.controllers.queries.get_uom";
            //     const filters = {
            //         item_name: frm.doc.item,
            //     };
            //     return { filters, query };
            // });

            // frm.set_query("diameter_uom", function() {
            //     const query = "powerpro.controllers.queries.get_uom";
            //     const filters = {
            //         item_name: frm.doc.item,
            //     };
            //     return { filters, query };
            // });

            // frm.set_query("capacity_uom", function() {
            //     const query = "powerpro.controllers.queries.get_uom";
            //     const filters = {
            //         item_name: frm.doc.item,
            //     };
            //     return { filters, query };
            // });

            // frm.set_query("weight_uom", function() {
            //     const query = "powerpro.controllers.queries.get_uom";
            //     const filters = {
            //         item_name: frm.doc.item,
            //     };
            //     return { filters, query };
            // });

            frm.set_query("voltage", function() {
                const query = "powerpro.controllers.queries.get_item_voltage";
                const filters = {
                    item_name: frm.doc.item,
                };
                return { filters, query };
            });

            frm.set_query("current", function() {
                const query = "powerpro.controllers.queries.get_item_current";
                const filters = {
                    item_name: frm.doc.item,
                };
                return { filters, query };
            });

            frm.set_query("phase", function() {
                const query = "powerpro.controllers.queries.get_item_phase";
                const filters = {
                    item_name: frm.doc.item,
                };
                return { filters, query };
            });

            // frm.set_query("capcidad_udm", function() {
            //     const query = "powerpro.controllers.queries.get_uom";
            //     const filters = {
            //         item_name: frm.doc.item,
            //     };
            //     return { filters, query };
            // });

            // frm.set_query("autonomy_uom", function() {
            //     const query = "powerpro.controllers.queries.get_uom";
            //     const filters = {
            //         item_name: frm.doc.item,
            //     };
            //     return { filters, query };
            // });

            frm.set_query("conectividad", function() {
                const query = "powerpro.controllers.queries.get_item_connectivity";
                const filters = {
                    item_name: frm.doc.item,
                };
                return { filters, query };
            });

            // frm.set_query("garantía_udm", function() {
            //     const query = "powerpro.controllers.queries.get_uom";
            //     const filters = {
            //         item_name: frm.doc.item,
            //     };
            //     return { filters, query };
            // });
        },
    
        setup_fields: function (frm) {
            if (frm.doc.item) {
                fetch_uom_categories(frm); // update the options available for UOMs
                
                // Configurar materiales, especificaciones, colores y usos
                //configure_item_fields(frm);
    
                // Mostrar/ocultar campos relacionados con "Item Name"
                frappe.call({
                    method: "frappe.client.get",
                    args: {
                        doctype: "Item Name",
                        name: frm.doc.item
                    },
                    callback: function (r) {
                        if (r.message) {
                            const selected_fields = r.message.fields || [];
    
                            frm.fields.forEach(field => {
                                if (
                                    field.df.fieldtype === "Column Break"
                                    || field.df.fieldtype === "Section Break"
                                    || field.df.fieldtype === "Tab Break"
                                    || field.df.fieldname === "description"
                                    || field.df.fieldname === "item"
                                ) {
                                    frm.set_df_property(field.df.fieldname, "hidden", false); // Siempre visible
                                } else {
                                    const is_visible = selected_fields.some(f => f.item_field_name === field.df.fieldname && f.item_show_field);
                                    frm.set_df_property(field.df.fieldname, "hidden", !is_visible);
    
                                    const is_obligatory = selected_fields.some(f => f.item_field_name === field.df.fieldname && f.item_obligatory_field);
                                    frm.set_df_property(field.df.fieldname, "reqd", is_obligatory);
                                }
                            });
    
                            frm.refresh(); // Aplicar cambios
                        }
                    }
                });
            } else {
                // Si no hay "item" seleccionado, limpiar todos los campos dependientes
                reset_fields(frm);
            }
        }
    });
    
    // Función para configurar materiales, especificaciones, colores y usos
    function configure_item_fields(frm) {
        // 1. Cargar materiales asociados
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Item Material",
                fields: ["item_material", "name"] // Obtener los nombres y los materiales
            },
            callback: function (r) {
                if (r.message && r.message.length > 0) {
                    const material_options = [];
    
                    // Verificar si el ítem está relacionado en la tabla `item_names`
                    r.message.forEach(row => {
                        frappe.call({
                            method: "frappe.client.get",
                            args: {
                                doctype: "Item Material",
                                name: row.name
                            },
                            callback: function (material_doc) {
                                if (material_doc.message) {
                                    const item_names = material_doc.message.item_names || [];
                                    const is_associated = item_names.some(item => item.item_name === frm.doc.item);
    
                                    if (is_associated) {
                                        material_options.push(row.item_material);
                                    }
    
                                    // Actualizar el campo "material" después de procesar todos los registros
                                    frm.set_df_property('material', 'options', material_options.join('\n'));
                                    frm.refresh_field('material');
                                }
                            }
                        });
                    });
                } else {
                    // Limpiar el campo "material" si no hay materiales asociados
                    frm.set_df_property('material', 'options', []);
                    frm.refresh_field('material');
                }
            }
        });
    
        // 2. Cargar especificaciones 1
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Item Specs 1",
                fields: ["name", "item_spec1_name"]
            },
            callback: function (r) {
                if (r.message) {
                    const spec1_options = [];
    
                    r.message.forEach(row => {
                        frappe.call({
                            method: "frappe.client.get",
                            args: {
                                doctype: "Item Specs 1",
                                name: row.name
                            },
                            callback: function (spec_data) {
                                if (spec_data.message) {
                                    const item_names = spec_data.message.item_names || [];
                                    const is_associated = item_names.some(item => item.item_name === frm.doc.item);
    
                                    if (is_associated) {
                                        spec1_options.push(row.item_spec1_name);
                                        frm.set_df_property('spec1', 'options', spec1_options.join('\n'));
                                        frm.refresh_field('spec1');
                                    }
                                }
                            }
                        });
                    });
                } else {
                    frm.set_df_property('spec1', 'options', []);
                    frm.refresh_field('spec1');
                }
            }
        });
    
        // 3. Cargar especificaciones 2
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Item Specs 2",
                fields: ["name", "item_spec2_name"]
            },
            callback: function (r) {
                if (r.message) {
                    const spec2_options = [];
    
                    r.message.forEach(row => {
                        frappe.call({
                            method: "frappe.client.get",
                            args: {
                                doctype: "Item Specs 2",
                                name: row.name
                            },
                            callback: function (spec_data) {
                                if (spec_data.message) {
                                    const item_names = spec_data.message.item_names || [];
                                    const is_associated = item_names.some(item => item.item_name === frm.doc.item);
    
                                    if (is_associated) {
                                        spec2_options.push(row.item_spec2_name);
                                        frm.set_df_property('spec2', 'options', spec2_options.join('\n'));
                                        frm.refresh_field('spec2');
                                    }
                                }
                            }
                        });
                    });
                } else {
                    frm.set_df_property('spec2', 'options', []);
                    frm.refresh_field('spec2');
                }
            }
        });
    
        // 4. Cargar colores
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Item Color",
                fields: ["name", "item_color"]
            },
            callback: function (r) {
                if (r.message) {
                    const color_options = [];
    
                    r.message.forEach(row => {
                        frappe.call({
                            method: "frappe.client.get",
                            args: {
                                doctype: "Item Color",
                                name: row.name
                            },
                            callback: function (color_data) {
                                if (color_data.message) {
                                    const item_names = color_data.message.item_names || [];
                                    const is_associated = item_names.some(item => item.item_name === frm.doc.item);
    
                                    if (is_associated) {
                                        color_options.push(row.item_color);
                                        frm.set_df_property('color', 'options', color_options.join('\n'));
                                        frm.refresh_field('color');
                                    }
                                }
                            }
                        });
                    });
                } else {
                    frm.set_df_property('color', 'options', []);
                    frm.refresh_field('color');
                }
            }
        });
    
        // 5. Cargar usos
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Item Use",
                fields: ["name", "item_use"]
            },
            callback: function (r) {
                if (r.message) {
                    const use_options = [];
    
                    r.message.forEach(row => {
                        frappe.call({
                            method: "frappe.client.get",
                            args: {
                                doctype: "Item Use",
                                name: row.name
                            },
                            callback: function (use_data) {
                                if (use_data.message) {
                                    const item_names = use_data.message.item_names || [];
                                    const is_associated = item_names.some(item => item.item_name === frm.doc.item);
    
                                    if (is_associated) {
                                        use_options.push(row.item_use);
                                        frm.set_df_property('use', 'options', use_options.join('\n'));
                                        frm.refresh_field('use');
                                    }
                                }
                            }
                        });
                    });
                } else {
                    frm.set_df_property('use', 'options', []);
                    frm.refresh_field('use');
                }
            }
        });
        
        
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Item Finish",
                fields: ["name", "item_finish"]
            },
            callback: function (r) {
                if (r.message) {
                    const finish_options = [];
    
                    r.message.forEach(row => {
                        frappe.call({
                            method: "frappe.client.get",
                            args: {
                                doctype: "Item Finish",
                                name: row.name
                            },
                            callback: function (use_data) {
                                if (use_data.message) {
                                    const item_names = use_data.message.item_names || [];
                                    const is_associated = item_names.some(item => item.item_name === frm.doc.item);
    
                                    if (is_associated) {
                                        finish_options.push(row.item_use);

                                        frm.set_df_property('finish', 'options', finish_options.join('\n'));
                                        frm.refresh_field('finish');
                                    }
                                }
                            }
                        });
                    });
                } else {
                    frm.set_df_property('finish', 'options', []);
                    frm.refresh_field('finish');
                }
            }
        });
    }
    
    // Función para reiniciar campos dependientes
    function reset_fields(frm) {
        frm.fields.forEach(field => {
            if (
                field.df.fieldtype === "Column Break"
                || field.df.fieldtype === "Section Break"
                || field.df.fieldname === "item"
            ) {
                frm.set_df_property(field.df.fieldname, "hidden", false);
            } else {
                frm.set_df_property(field.df.fieldname, "hidden", true);
                frm.set_df_property(field.df.fieldname, "reqd", false);
                frm.doc[field.df.fieldname] = null;
            }
        });
    
        // frm.set_df_property('material', 'options', []);
        // frm.refresh_field('material');
        
        // frm.set_df_property('spec1', 'options', []);
        // frm.refresh_field('spec1');

        // frm.set_df_property('spec2', 'options', []);
        // frm.refresh_field('spec2');
        
        // frm.set_df_property('color', 'options', []);
        // frm.refresh_field('color');
        
        // frm.set_df_property('use', 'options', []);
        // frm.refresh_field('use');
        
        frm.refresh();
    }
}
