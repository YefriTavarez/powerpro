// PowerPro: Extend Delivery Note to fetch items from multiple Projects
/* eslint-disable */

frappe.ui.form.on('Delivery Note', {
    refresh(frm) {
        if (frm.is_new() || frm.doc.docstatus === 0) {
            add_projects_fetch_button_dn(frm);
        }
    }
});

function add_projects_fetch_button_dn(frm) {
    frm.add_custom_button(
        __('Projects'),
        () => open_projects_multiselect_dn(frm),
        __('Get Items From')
    );
}

function open_projects_multiselect_dn(frm) {
    const d = new frappe.ui.form.MultiSelectDialog({
        doctype: 'Project',
        target: frm,
        setters: {},
        get_query() {
            return {
                filters: [
                    ['Project', 'sales_order', 'is', 'set'],
                ].concat(frm.doc.company ? [['Project','company','=','' + frm.doc.company]] : [])
            };
        },
        size: 'large',
        action(selections) {
            if (!selections || !selections.length) {
                d.dialog.hide();
                return;
            }
            const method = 'powerpro.controllers.project.project.get_delivery_note_items_from_projects';
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
