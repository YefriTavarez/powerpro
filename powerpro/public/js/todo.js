

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
            const allowed_doctypes = [
                "Asset Maintenance Task",
                "Training Event",
            ];

            if (doc.status == "Open" && allowed_doctypes.includes(doc.reference_type)) {
                frm.add_custom_button(
                    __("Close"),
                    function () {
                        if (doc.reference_type == "Asset Maintenance Task") {
                            if (!doc.actions_performed) {
                                frappe.throw(
                                    "Debe especificar las acciones realizadas durante esta tarea para poder cerrar el mantenimiento."
                                )
                            }

                            if (doc.__unsaved) {
                                frappe.throw(
                                    "Por favor guarde el registro antes de cerrar la tarea."
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
                        } else if (doc.reference_type == "Training Event") {
                            frappe.confirm(
                                __("¿Está seguro que desea cerrar y firmar su asistencia a este evento?"),
                                function () {
                                    frm.set_value("status", "Closed");
                                    frm.save(null, function () {
                                        // back to list
                                        frappe.set_route("List", "ToDo");
                                    });
                                }
                            );
                        } 
                        else {
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
                if (doc.status == "Cancelled" && doc.reference_type == "Asset Maintenance Task") {
                    return;
                }

                frm.add_custom_button(
                    __("Reopen"),
                    function () {
                        if (doc.reference_type == "Asset Maintenance Task") {
                            const method = "powerpro.controllers.todo.reopen_maintenance_task";
                            const args = {
                                "todo": doc.name, 
                                "task": doc.reference_name,
                                "due_date": doc.date,
                            };
                            const callback = function () {
                                // frm.set_value("status", "Open");
                                frm.reload_doc();
                            }

                            frappe.call({ method, args, callback });
                        }
                        // frm.save();
                    },
                    null,
                    "btn-default"
                );
            }
            // frm.add_custom_button(
            //     __("New"),
            //     function () {
            //         frappe.new_doc("ToDo");
            //     },
            //     null,
            //     "btn-default"
            // );
        }
    },
});