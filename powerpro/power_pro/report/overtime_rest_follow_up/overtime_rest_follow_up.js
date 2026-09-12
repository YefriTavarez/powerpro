frappe.query_reports["Overtime Rest Follow Up"] = {
    filters: [
        {fieldname: "company", label: __("Empresa"), fieldtype: "Link", options: "Company"},
        {fieldname: "employee", label: __("Empleado"), fieldtype: "Link", options: "Employee"},
        {fieldname: "from_date", label: __("Fin del descanso desde"), fieldtype: "Date"},
        {fieldname: "to_date", label: __("Fin del descanso hasta"), fieldtype: "Date"},
        {fieldname: "include_enjoyed", label: __("Incluir descansos disfrutados"), fieldtype: "Check", default: 0}
    ]
};
