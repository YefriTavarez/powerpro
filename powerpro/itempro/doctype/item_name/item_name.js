// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt

{
    function refresh(frm) {
        frm.add_custom_button(__('Populate Fields'), function () {
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "DocType",
                    name: "Item Generator" // Asegúrate de que este Doctype existe
                },
                callback: function (r) {
                    if (r.message && r.message.fields) {
                        const fields = r.message.fields;

                        // Filtrar campos válidos
                        const valid_fields = fields.filter(field => {
                            return field.fieldtype !== "Column Break" &&
                                   field.fieldtype !== "Section Break" &&
                                   field.fieldtype !== "Tab Break" &&
                                   field.fieldname !== "item" &&
                                   field.fieldname !== "description" &&
                                   field.fieldname !== "amended_from" &&
                                   field.fieldname !== "smart_hash"
                                ; // Excluir el campo "item"
                        });

                        // Limpiar la tabla existente
                        frm.clear_table('fields');

                        // Poblar la tabla con los campos válidos
                        valid_fields.forEach(field => {
                            let row = frm.add_child('fields');
                            row.item_field_name = field.fieldname || ''; // Asignar nombre del campo
                            
                            row.field_type = field.fieldtype;
                            if (field.fieldtype === "Link") {
                                row.options = field.options;
                            } else {
                                row.options = null;
                            }
                            row.item_show_field = 0; // Por defecto, no mostrar
                        });

                        // Refrescar la tabla
                        frm.refresh_field('fields');

                        // Mostrar un mensaje
                        frappe.msgprint(__('Fields populated successfully.'));
                    } else {
                        frappe.msgprint(__('No fields found in the selected Doctype.'));
                    }
                }
            });
        });
    }
    
    function onload(frm) {
        _load_item_groups(frm);
        _set_queries_on_item_groups(frm);
    }
    
    let all_item_groups;

    function _load_item_groups(frm) {
        _toggle_display_on_item_groups(frm);

        if (!all_item_groups) {
            frappe.call({
                method: "igcaribe.client.get_all_item_groups",
                args: { /* no args */ },
                callback({ message }) {
                    all_item_groups = message;

                    _toggle_display_on_item_groups(frm);
                },
            });
        }
    }

    const item_group_fields = [
        "item_group_1",
        "item_group_2",
        "item_group_3",
        "item_group_4",
        "item_group_5",
    ];

    function _toggle_display_on_item_groups(frm) {
        const { doc } = frm;

        const loaded_item_groups = Boolean(all_item_groups);
        
        // const group_map = all_item_groups || {};
        
        
        
        const display_condition_map = {
            "item_group_1": true, // always display first Item Group
            "item_group_2": Boolean(doc.item_group_1) && __get_children_of(doc.item_group_1)?.length,
            "item_group_3": Boolean(doc.item_group_2) && __get_children_of(doc.item_group_2)?.length,
            "item_group_4": Boolean(doc.item_group_3) && __get_children_of(doc.item_group_3)?.length,
            "item_group_5": Boolean(doc.item_group_4) && __get_children_of(doc.item_group_4)?.length,
        };
        
        for (const fieldname of item_group_fields) {
            const display = loaded_item_groups && display_condition_map[fieldname];
            frm.toggle_display(fieldname, display);
            
            // temporary solution
            frm.toggle_reqd(fieldname, display);
        }
    }

    function item_group_1(frm) {
        _toggle_display_on_item_groups(frm);

        frm.set_value("item_group_2", "");
    }

    function item_group_2(frm) {
        _toggle_display_on_item_groups(frm);
        
        frm.set_value("item_group_3", "");
    }

    function item_group_3(frm) {
        _toggle_display_on_item_groups(frm);
        
        frm.set_value("item_group_4", "");
    }

    function item_group_4(frm) {
        _toggle_display_on_item_groups(frm);
        
        frm.set_value("item_group_5", "");
    }

    function item_group_5(frm) {
        _toggle_display_on_item_groups(frm);
        
        // frm.set_value("item_group_6", "");
    }

    function _set_queries_on_item_groups(frm) {
        const { doc } = frm;

        frm.set_query("item_group_1", function() {
            const filters = {
                parent_item_group: __get_root_item_group(),
            };
            
            return { filters };
        });

        frm.set_query("item_group_2", function() {
            const filters = {
                parent_item_group: doc.item_group_1,
            };

            return { filters };
        });

        frm.set_query("item_group_3", function() {
            const filters = {
                parent_item_group: doc.item_group_2,
            };
            
            return { filters };
        });

        frm.set_query("item_group_4", function() {
            const filters = {
                parent_item_group: doc.item_group_3,
            };
            
            return { filters };
        });

        frm.set_query("item_group_5", function() {
            const filters = {
                parent_item_group: doc.item_group_4,
            };
            
            return { filters };
        });
    }
    
    function __get_root_item_group() {
        if (!all_item_groups) {
            return null;
        }
        
        let root_item_group;
        for (const key in all_item_groups) {
            const item_group = all_item_groups[key];
            
            if (item_group.is_group && !item_group.parent_item_group) {
                root_item_group = item_group.name;
                break;
            }
        }
        
        return root_item_group;
    }
    
    function __get_children_of(parent_item_group) {
        const out = new Array();

        const group_map = all_item_groups || {};

        for (const item_group_id in group_map) {
            const item_group = all_item_groups[item_group_id];
            
            if (item_group.parent_item_group === parent_item_group) {
                out.push(item_group_id);
            }
        }
        
        return out;
    }
    
    frappe.ui.form.on('Item Name', {
        onload,
        refresh,
        item_group_1,
        item_group_2,
        item_group_3,
        item_group_4,
        item_group_5,
    });
}