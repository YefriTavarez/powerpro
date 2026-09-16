"""Install metadata only. Never enable the feature, create payroll, or adopt legacy salaries."""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from powerpro.supplements.rules import FIELDS


def execute():
    for name in ('employee_supplement_mapping', 'employee_supplement_existing_salary',
                 'employee_supplement_revision', 'employee_supplement_settings'):
        frappe.reload_doc('power_pro', 'doctype', name)
    # Preserve customer-owned Currency fields exactly when they already exist.
    previous = 'ctc'
    employee = []
    for name, label in FIELDS.items():
        if not frappe.get_meta('Employee').has_field(name):
            employee.append(dict(fieldname=name, label=label, fieldtype='Currency',
                                 options='salary_currency', insert_after=previous))
        previous = name
    employee.append(dict(fieldname='pp_supplements_effective_from', label='Cambio de complementos vigente desde',
                         fieldtype='Date', insert_after=previous, no_copy=1,
                         description='Fecha inicial del nuevo importe mensual. No altera períodos ya preparados.'))
    create_custom_fields({'Employee': employee}, update=False)
    create_custom_fields({
        'Salary Slip': [dict(fieldname='pp_employee_supplements', label='Registro de complementos aplicados',
                            fieldtype='Long Text', read_only=1, no_copy=1, hidden=1)],
        'Additional Salary': [
            dict(fieldname='pp_supplement_payroll_entry', label='Nómina de origen del complemento', fieldtype='Data', read_only=1, no_copy=1),
            dict(fieldname='pp_supplement_treatment', label='Tratamiento del complemento', fieldtype='Select',
                 options='\nIndependent', insert_after='salary_component', allow_on_submit=1,
                 description='Independent: pago separado que se suma al complemento fijo. Los recurrentes que lo cubren se asocian en Employee Supplement Settings.'),
            dict(fieldname='pp_supplement_key', label='Clave del complemento automático', fieldtype='Data',
                 read_only=1, no_copy=1, unique=1),
            dict(fieldname='pp_supplement_field', label='Campo de origen', fieldtype='Data',read_only=1,no_copy=1),
            dict(fieldname='pp_supplement_start', label='Inicio del período del complemento', fieldtype='Date',read_only=1,no_copy=1),
            dict(fieldname='pp_supplement_end', label='Fin del período del complemento', fieldtype='Date',read_only=1,no_copy=1),
            dict(fieldname='pp_supplement_monthly', label='Importe mensual de origen', fieldtype='Currency',read_only=1,no_copy=1),
        ],
    }, update=False)
    settings = frappe.get_single('Employee Supplement Settings')
    if not settings.mappings:
        for field in FIELDS:
            settings.append('mappings', dict(source_field=field))
        settings.save(ignore_permissions=True)
