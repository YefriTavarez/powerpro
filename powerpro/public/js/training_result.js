
frappe.ui.form.on("Training Result", {
    refresh: function(frm) {
        frm.trigger("set_queries");
        frm.trigger("set_present_employess");
    },

    training_event: function(frm) {
        frm.trigger("set_present_employess");
    },

    set_queries: function(frm) {
        frm.trigger("training_event_set_query");
    },

    training_event_set_query: function(frm) {
        frm.set_query("training_event", function() {
            return {
                filters: {
                    docstatus: 1,
                }
            };
        });
    },

    set_present_employess: function(frm) {
        const { doc } = frm;

        if (!frm.is_new()) {
            return;
        }

        if (!doc.training_event) {
            return;
        }

        const method = "powerpro.controllers.training_result.get_present_employees";
        const args = { training_event: doc.training_event };
        const callback = function(response) {
            const { message } = response;

            // message is an object that has the employee, employee_name and department fields
            // add each employee to the table
            frm.clear_table("employees");

            message.forEach(function(employee) {
                frm.add_child("employees", {
                    employee: employee.employee,
                    employee_name: employee.employee_name,
                    department: employee.department
                });
            });

            frm.refresh_field("employees");

        };

        frappe.call({ method, args, callback });
    }
});