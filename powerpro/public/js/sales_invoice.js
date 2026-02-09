// PowerPro: Extend Sales Invoice to fetch items from multiple Projects
/* eslint-disable */

frappe.ui.form.on('Sales Invoice', {
    refresh(frm) {
        if (frm.is_new() || frm.doc.docstatus === 0) {
            add_projects_fetch_button(frm);
        }
    }
});

function add_projects_fetch_button(frm) {
    frm.add_custom_button(
        __('Projects'),
        () => open_projects_multiselect(frm, 'si'),
        __('Get Items From')
    );
}

function open_projects_multiselect(frm, target_type) {
    const filters = { };
    if (frm.doc.company) filters['company'] = frm.doc.company;
    // Only projects that have a linked Sales Order and sku_producto
    const d = new frappe.ui.form.MultiSelectDialog({
        doctype: 'Project',
        target: frm,
        sales_order: "",
        sku_producto: "",
        arte: "",
        setters: [
            { fieldname: 'sales_order', fieldtype: 'Link', options: 'Sales Order', label: __('Sales Order'), get_query() {
                return {
                    filters: [
                        ['Sales Order', 'customer', '=', frm.doc.customer || ""],
                    ].concat(frm.doc.company ? [['Sales Order','company','=','' + frm.doc.company]] : [])
                };
            } },
            { fieldname: 'sku_producto', fieldtype: 'Link', options: 'Item', label: __('SKU Producto'), get_query() {
                return {
                    filters: [
                        ['Item', 'item_code', 'is', 'set'],
                    ].concat(frm.doc.company ? [['Item','company','=','' + frm.doc.company]] : [])
                };
            } },
            { fieldname: 'arte', fieldtype: 'Link', options: 'Item', label: __('Arte'), get_query() {
                return {
                    filters: [
                        ['Arte', ' name', 'is', 'set'],
                    ].concat(frm.doc.company ? [['Item','company','=','' + frm.doc.company]] : [])
                };
            } },
        ],
        get_query() {
            return {
                filters: [
                    ['Project', 'sales_order', 'is', 'set'],
                    ['Project', 'customer', '=', frm.doc.customer || ""],
                ].concat(frm.doc.company ? [['Project','company','=','' + frm.doc.company]] : [])
            };
        },
        size: 'large',
        action(selections) {
            if (!selections || !selections.length) {
                d.dialog.hide();
                return;
            }
            const method = 'powerpro.controllers.project.project.get_sales_invoice_items_from_projects';
            frappe.call({
                method,
                args: { projects: selections },
            }).then(r => {
                const data = r.message || {};
                const items = data.items || [];
                const errors = data.errors || [];

                for (const it of items) {
                    const row = frm.add_child('items');
                    Object.assign(row, it);
                }
                frm.refresh_field('items');
                if (errors.length) {
                    frappe.msgprint({
                        title: __('Some projects were skipped'),
                        message: '<ul>' + errors.map(e => `<li>${frappe.utils.escape_html(e)}</li>`).join('') + '</ul>',
                        indicator: 'orange'
                    });
                }
            }).always(() => {
                d.dialog.hide();
            });
        }
    });
}
