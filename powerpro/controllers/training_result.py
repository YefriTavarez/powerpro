
import frappe


@frappe.whitelist()
def get_present_employees(training_event):
    training_event = get_training_event(training_event)
    employees = []

    if not training_event:
        return

    for employee in training_event.employees:
        if employee.attendance == "Present":
            # set employee, employee_name, and department
            employees.append({
                "employee": employee.employee,
                "employee_name": employee.employee_name,
                "department": employee.department,
            })

    return employees


def get_training_event(training_event):
    doctype = "Training Event"

    if name := frappe.db.exists(doctype, training_event):
        return frappe.get_doc(doctype, name)