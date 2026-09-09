"""Read-only rollout evidence; never print site config or credentials."""
import os

import frappe

TARGETS = ['Overtime Work Call', 'Overtime Work Call Date', 'Overtime Authorization',
           'Employee', 'IGC Settings', 'Journal Entry', 'Solicitud de Dieta', 'Lote de Pago de Dietas']


def inspect():
    apps = frappe.get_installed_apps()
    result = {'site': frappe.local.site, 'bench_path': os.path.abspath(os.path.join(frappe.get_site_path(), '..', '..')),
              'environment': 'Production unless independently confirmed otherwise',
              'installed_apps_in_order': apps,
              'versions': {app: getattr(frappe.get_module(app), '__version__', 'unknown') for app in apps},
              'doctypes': {}}
    for dt in TARGETS:
        if not frappe.db.exists('DocType', dt):
            result['doctypes'][dt] = {'installed': False}
            continue
        meta = frappe.get_meta(dt)
        result['doctypes'][dt] = {
            'installed': True, 'module': meta.module, 'custom': meta.custom,
            'fields': [{'fieldname': f.fieldname, 'fieldtype': f.fieldtype, 'options': f.options,
                        'reqd': f.reqd, 'read_only': f.read_only, 'allow_on_submit': f.allow_on_submit} for f in meta.fields],
            'permissions': [p.as_dict() for p in meta.permissions],
            'custom_fields': frappe.get_all('Custom Field', filters={'dt': dt}, fields=['name','fieldname','fieldtype','options']),
            'property_setters': frappe.get_all('Property Setter', filters={'doc_type':dt}, fields=['name','field_name','property','value']),
            'client_scripts': frappe.get_all('Client Script', filters={'dt':dt}, fields=['name','enabled']),
            'server_scripts': frappe.get_all('Server Script', filters={'reference_doctype':dt}, fields=['name','disabled','script_type']),
            'workflows': frappe.get_all('Workflow', filters={'document_type':dt}, fields=['name','is_active']),
            'hooks': {key: frappe.get_hooks(key).get(dt) for key in ('doc_events','override_doctype_class','has_permission','permission_query_conditions')},
        }
    result['wildcard_doc_events'] = frappe.get_hooks('doc_events').get('*')
    result['recent_errors'] = frappe.get_all('Error Log', fields=['name','method','creation'], order_by='creation desc', limit_page_length=10)
    result['work_call_sample'] = frappe.get_all('Overtime Work Call', fields=['name','docstatus','status','from_date','to_date'], order_by='creation desc', limit_page_length=5)
    result['settings'] = frappe.get_single('IGC Settings').get('dieta_companies') or []
    return result
