
frappe.ui.form.off("refresh", "Asset Maintenance");
frappe.ui.form.off("make_dashboard", "Asset Maintenance");

frappe.ui.form.on("Asset Maintenance", {
    on_load: function(frm) {
        frm.trigger("make_dashboard");
    },

    refresh: function(frm) {
        frm.trigger("add_custom_buttons");
        frm.trigger("set_read_only_fields");
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

    make_dashboard: (frm) => {
        const { doc } = frm;
    
        if (!frm.is_new()) {
            frappe.call({
                method: "powerpro.controllers.asset_maintenance.make_dashboard",
                args: { 
                    asset_name: doc.asset_name,
                    maintenance_team: doc.maintenance_team,
                },
                callback: (r) => {
                    if (!r.message) {
                        return;
                    }
    
                    // Eliminar la sección original si existe
                    $('div.section-head:contains("Maintenance Log")')
                        .closest('div.form-dashboard-section')
                        .remove();
    
                    // Crear una nueva sección con un id único
                    const sectionId = "custom-maintenance-log";
                    const section = frm.dashboard.add_section("", __("Maintenance Log"));
                    $(section).attr("id", sectionId); // Asignar un id único
    
                    var rows = $("<div></div>").appendTo(section);
    
                    // Renderizar cada log con el formato de indicador
                    (r.message || []).forEach(function (d) {
                        let indicatorClass = "gray";
                        let statusText = __(d.maintenance_status);
    
                        // Determinar el texto e indicador según el docstatus y maintenance_status
                        if (d.docstatus == 0) {
                            indicatorClass = "blue";
                            statusText = __("Draft");
                        }
    
                        if (d.maintenance_status === "Planned") {
                            if (d.docstatus == 1) {
                                indicatorClass = "orange";
                                statusText = __("Planned and Submitted");
                            }
                        }
    
                        if (d.maintenance_status === "Completed") {
                            indicatorClass = "green";
                            statusText = __("Completed");
                        }
    
                        if (d.maintenance_status === "Overdue") {
                            indicatorClass = "red";
                            statusText = __("Overdue");
                        }
    
                        if (d.maintenance_status === "Cancelled") {
                            indicatorClass = "gray";
                            statusText = __("Cancelled");
                        }
    
                        $(`<div class='row' style='margin-bottom: 10px;'>
                            <div class='col-sm-3 small'>
                                <a onclick="frappe.set_route('List', 'Asset Maintenance Log',
                                    {
                                        'asset_name': '${d.asset_name}',
                                        'maintenance_status': '${d.maintenance_status}',
                                        'maintenance_team': '${doc.maintenance_team}',
                                        'docstatus': '${d.docstatus}',
                                    });">
                                    <span class="indicator-pill no-indicator-dot whitespace-nowrap ${indicatorClass}">
                                        <span>${statusText}</span>
                                    </span> 
                                    <span class="badge" style="font-size: 12px">${d.count}</span>
                                </a>
                            </div>
                        </div>`).appendTo(rows);
                    });
    
                    frm.dashboard.show();
                },
            });
        }
    },
    set_read_only_fields: function(frm) {
        frm.trigger("set_read_only_asset_name");
    },

    set_read_only_asset_name: function(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.set_df_property("asset_name", "read_only", 1);
    },


});

