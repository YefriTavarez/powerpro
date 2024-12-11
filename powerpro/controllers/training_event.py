

import frappe
from . import assign_to


def on_submit(doc, method):
    assing_task_to_employees(doc)


def on_cancel(doc, method):
    cancel_assigned_tasks(doc)


def assing_task_to_employees(doc):
    for employee in doc.employees:
        if employee.attendance != "Present":
            continue

        user_id = get_employee_user_id(employee.employee)

        if not user_id:
            frappe.throw(
                f"""El empleado <b>{employee.employee_name}</b> no tiene configurado un usuario en el sistema. 
                Favor de agregar un usuario para asignar la tarea."""
            )

        args = {
            "doctype": "Training Event",
            "assign_to": user_id,
            "assigne_name": employee.employee_name,
            "name": doc.name,
            "description": f"<h3>Agregar Firma de Asistencia al Evento de Capacitación - {doc.name}</h3><br>{doc.introduction}",
            "date": str(doc.end_time),
        }
        args["assign_to"] = [args["assign_to"]]
        assign_to.add(args, ignore_permissions=True)



def cancel_assigned_tasks(doc):
    doctype = "ToDo"
    todos = get_training_event_todos(doctype, doc.name)

    if not todos:
        return

    for todo in todos:
        doc = frappe.get_doc(doctype, todo.name)
        doc.status = "Cancelled"
        doc.ignore_permissions = True
        doc.save()


def get_training_event_todos(doctype, training_event):
    filters = {
        "reference_type": "Training Event",
        "reference_name": training_event,
    }

    return frappe.get_all(doctype, filters=filters)


def get_employee_user_id(employee):
    doctype = "Employee"
    filters = {
        "name": employee,
    }
    fields = ["user_id"]

    return frappe.get_value(doctype, filters=filters, fieldname=fields)

