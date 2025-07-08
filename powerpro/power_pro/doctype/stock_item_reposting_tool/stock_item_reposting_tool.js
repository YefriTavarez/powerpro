// Copyright (c) 2024, Yefri Tavarez and contributors
// For license information, please see license.txt

frappe.ui.form.on('Stock Item Reposting Tool', {
    refresh: function(frm) {
        // // Add custom button for execution
        // frm.add_custom_button(__('Execute Tool'), function() {
        //     execute_reposting_tool(frm);
        // }, __('Actions'));
        
        // Set button styling
        frm.page.set_primary_action(__('Execute Tool'), function() {
            execute_reposting_tool(frm);
        });

        frm.set_query("item", function(doc, cdt, cdn) {
            return {
                filters: {
                    is_stock_item: 0, // Only show non-stock items
                    disabled: 0,
                }
            }
        });

        frm.set_query("item_group", function(doc, cdt, cdn) {
            return {
                filters: {
                    is_group: 0,
                }
            }
        });
    },
    
    mode: function(frm) {
        // Clear fields when mode changes
        if (frm.doc.mode === 'Individual') {
            frm.set_value('item_group', '');
            frm.set_value('item_list_paste', '');
        } else if (frm.doc.mode === 'Batch') {
            frm.set_value('item', '');
        }
        frm.refresh_fields();
    },
    
    dry_run: function(frm) {
        // Update button text based on dry run status
        update_button_text(frm);
    },

    _item_group: function(frm) {
        console.log(frm.doc.item_group);

        if (frm.doc.item_group) {
            frm.set_value("item", "");
        }

        frm.dashboard.clear_comment();

        if (frm._last_item_group === frm.doc.item_group) {
            return; // Prevent multiple calls to the same function
        }
        frm._last_item_group = frm.doc.item_group;

        // Show item count for selected group
        if (frm.doc.item_group) {
            frappe.call({
                method: 'frappe.client.get_count',
                args: {
                    doctype: 'Item',
                    filters: {
                        'item_group': frm.doc.item_group,
                        'disabled': 0
                    }
                },
                callback: async function(r) {
                    await frappe.timeout(.5);
                    // if (r.message) {
                    //     console.log(r.message);
                    //     frm.dashboard.add_comment(__('Items in group: {0}', [r.message]), 'blue', true);
                    // }
                }
            });
        }
    },
});

function execute_reposting_tool(frm) {
    // Validation before execution
    if (!validate_form(frm)) {
        return;
    }
    
    // Show confirmation dialog
    let message = frm.doc.dry_run ? 
        __('This will perform a dry run simulation. No actual changes will be made.') :
        __('This will modify stock item settings and may affect stock transactions. Are you sure?');
    
    frappe.confirm(
        message,
        function() {
            // User confirmed, proceed with execution
            frm.call('execute_tool').then(r => {
                if (r.message) {
                    frappe.msgprint({
                        title: __('Execution Complete'),
                        message: r.message.message || __('Tool executed successfully'),
                        indicator: 'green'
                    });
                }
            });
        },
        function() {
            // User cancelled
            frappe.msgprint(__('Execution cancelled'));
        }
    );
}

function validate_form(frm) {
    // Check if target stock status is selected
    // if (!frm.doc.target_stock_status) {
    //     frappe.msgprint(__('Please select a Target Stock Status'));
    //     return false;
    // }
    
    // Mode-specific validation
    if (frm.doc.mode === 'Individual') {
        if (!frm.doc.item) {
            frappe.msgprint(__('Please select an Item for Individual mode'));
            return false;
        }
    } else if (frm.doc.mode === 'Batch') {
        if (!frm.doc.item_group && !frm.doc.item_list_paste) {
            frappe.msgprint(__('Please select an Item Group or paste Item List for Batch mode'));
            return false;
        }
    }
    
    return true;
}

function update_button_text(frm) {
    let button_text = frm.doc.dry_run ? __('Run Simulation') : __('Execute Tool');
    
    // Update primary action button
    frm.page.set_primary_action(button_text, function() {
        execute_reposting_tool(frm);
    });
}

// Additional utility functions for enhanced UX
frappe.ui.form.on('Stock Item Reposting Tool', {
    item_list_paste: function(frm) {
        frm.dashboard.clear_comment();
        
        // Count items in pasted list
        if (frm.doc.item_list_paste) {
            let lines = frm.doc.item_list_paste.split('\n').filter(line => line.trim());
            if (lines.length > 0) {
                frm.dashboard.add_comment(__('Items in list: {0}', [lines.length]), 'blue');
            }
        }
    },
    
    item_group: function(frm) {
        // Show item count for selected group
        if (frm.doc.item_group) {
            frappe.call({
                method: 'frappe.client.get_count',
                args: {
                    doctype: 'Item',
                    filters: {
                        'item_group': frm.doc.item_group,
                        'disabled': 0
                    }
                },
                callback: function(r) {
                    if (
                        typeof r.message === 'number'
                    ) {
                        frm.dashboard.add_comment(__('Items in group: {0}', [r.message]), 'blue');

                        if (r.message > 0) {
                            // fill item list with items in group
                            frm.add_custom_button("Fill Item List", function() {
                                frm.trigger('fill_item_list_paste');
                            });
                        }
                    }
                },
            });
        }
    },

    fill_item_list_paste: function(frm) {
        // fill item list with items in group
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Item',
                filters: {
                    'item_group': frm.doc.item_group,
                    'disabled': 0
                }
            },
            callback: function(r) {
                if (r.message) {
                    frm.set_value('item_list_paste', r.message.map(item => item.name).join('\n'));
                }
            }
        });
    }
});
