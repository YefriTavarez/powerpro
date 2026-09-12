frappe.query_reports['Overtime Evidence Follow Up'] = {filters: [
    {fieldname:'company',label:__('Empresa'),fieldtype:'Link',options:'Company'},
    {fieldname:'employee',label:__('Empleado'),fieldtype:'Link',options:'Employee'},
    {fieldname:'responsible',label:__('Responsable'),fieldtype:'Link',options:'User'},
    {fieldname:'from_date',label:__('Desde'),fieldtype:'Date'},
    {fieldname:'to_date',label:__('Hasta'),fieldtype:'Date'},
    {fieldname:'include_current',label:__('Incluir evidencia vigente'),fieldtype:'Check',default:0}
]};
