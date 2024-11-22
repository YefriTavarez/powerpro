
frappe.ui.form.on("Asset Maintenance", {
    refresh: function(frm) {
        frm.trigger("add_custom_buttons");
    },

    add_custom_buttons: function(frm) {
        frm.trigger("add_submit_logs_button");
    },

    add_submit_logs_button: function(frm) {
        if (frm.is_new()) {
            return;
        }

        const { doc } = frm;

        const label = __("Validar Registros de Mantenimiento");
        const action = () => {
            frappe.call({
                method: "powerpro.controllers.asset_maintenance.submit_logs",
                args: { 
                    asset_maintenance: doc.name,
                },
                callback: () => {
                    frm.reload_doc();
                    frappe.msgprint(__("Registros de Mantenimiento validados correctamente."));
                }
            });
        };
        const bt_class = "btn-primary";

        frm.add_custom_button(label, action).addClass(bt_class);
    },
});