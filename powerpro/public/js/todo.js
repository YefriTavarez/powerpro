

frappe.ui.form.off("ToDo", "refresh");

frappe.ui.form.on("ToDo", {
    refresh: function (frm) {
        const { doc } = frm;

        if (doc.reference_type != "Asset Maintenance Task" && doc.reference_name) {
            frm.add_custom_button(__(doc.reference_name), function () {
                frappe.set_route("Form", doc.reference_type, doc.reference_name);
            });
        }

        if (!doc.__islocal) {
            if (doc.status == "Open" && doc.reference_type == "Asset Maintenance Task") {
                frm.add_custom_button(
                    __("Close"),
                    function () {
                        if (doc.reference_type == "Asset Maintenance Task") {
                            if (!doc.actions_performed) {
                                frappe.throw(
                                    "Debe especificar las acciones realizadas durante esta tarea para poder cerrar el mantenimiento."
                                )
                            }
                                
                            const method = "powerpro.controllers.todo.close_maintenance_task";
                            const args = {
                                "todo": doc.name, 
                                "task": doc.reference_name,
                                "due_date": doc.date,
                            };
                            const callback = function () {
                                frm.reload_doc();
                            }

                            frappe.call({ method, args, callback });
                        } else {
                            frm.set_value("status", "Closed");
                            frm.save(null, function () {
                                // back to list
                                frappe.set_route("List", "ToDo");
                            });
                        }
                    },
                    "fa fa-check",
                    "btn-success"
                );
            } else {
                frm.add_custom_button(
                    __("Reopen"),
                    function () {
                        frm.set_value("status", "Open");
                        frm.save();
                    },
                    null,
                    "btn-default"
                );
            }
            frm.add_custom_button(
                __("New"),
                function () {
                    frappe.new_doc("ToDo");
                },
                null,
                "btn-default"
            );
        }
    },
});