"""Explicit, idempotent installation. Existing edited scripts are never overwritten."""
import json
from pathlib import Path
import frappe

ROOT = Path(__file__).resolve().parent
NATIVE = ['Shift Assignment', 'Overtime Work Call', 'Retroactive Overtime Adjustment', 'Ordinary Night Settlement']


def specs():
    read = lambda name: (ROOT / name).read_text()
    servers = [dict(doctype='Server Script', name='IGC - Registro de Jornada - Validación V1',
        script_type='DocType Event', reference_doctype='Registro de Jornada', doctype_event='Before Save',
        disabled=0, script=read('jornada_validate.py')),
        dict(doctype='Server Script', name='IGC - Registro de Jornada - API V1', script_type='API',
             api_method='igc_journey_register_v1', allow_guest=0, disabled=0, script=read('jornada_api.py'))]
    for dt in NATIVE:
        for event in ['Before Save', 'Before Submit'] + (['Before Cancel'] if dt == 'Shift Assignment' else []):
            servers.append(dict(doctype='Server Script', name=f'IGC - Jornada - {dt} - {event} V1',
                script_type='DocType Event', reference_doctype=dt, doctype_event=event, disabled=0,
                script=read('jornada_source_guard.py').replace('FINANCIAL_GUARD', 'False' if event == 'Before Save' else 'True')))
    clients = [dict(doctype='Client Script', name='IGC - Registro de Jornada - '+suffix+' V1',
                    dt=dt, view='Form', enabled=0, script=read(filename))
        for suffix, dt, filename in [('Interfaz', 'Registro de Jornada', 'jornada_client.js'),
            ('Desde Convocatoria', 'Overtime Work Call', 'jornada_entry_workcall.js'),
            ('Desde Nómina', 'Payroll Entry', 'jornada_entry_payroll.js')]]
    return servers, clients


def install(enable_ui=False):
    """Run after deploying the Python adapter; UI opt-in follows staging verification."""
    frappe.only_for('System Manager')
    from powerpro.controllers.registered_journey import VERSION
    if VERSION != 1:
        frappe.throw('Versión de Registro de Jornada incompatible.')
    for schema in json.loads((ROOT / 'schema.json').read_text()):
        if not frappe.db.exists('DocType', schema['name']):
            frappe.get_doc(schema).insert()
        else:
            existing = frappe.get_doc('DocType', schema['name'])
            if not existing.custom:
                frappe.throw('El DocType existente no corresponde a este instalador: '+schema['name'])
            fields = {f.fieldname: f for f in existing.fields}
            for field in schema['fields']:
                current = fields.get(field['fieldname'])
                if not current or any((current.get(k) or '') != (field.get(k) or '') for k in ['fieldtype', 'options']):
                    frappe.throw('Revise el esquema existente antes de actualizar: '+schema['name']+'.'+field['fieldname'])
    for dt in NATIVE:
        after = frappe.get_meta(dt).fields[-1].fieldname
        for field in [dict(fieldname='custom_igc_journey', label='Registro de Jornada', fieldtype='Link', options='Registro de Jornada'),
                      dict(fieldname='custom_igc_journey_row', label='Fila de Jornada', fieldtype='Data', hidden=1),
                      dict(fieldname='custom_igc_journey_key', label='Clave de Jornada', fieldtype='Data', hidden=1, unique=1)]:
            field.update(doctype='Custom Field', dt=dt, read_only=1, no_copy=1, insert_after=after)
            name = dt+'-'+field['fieldname']
            if frappe.db.exists('Custom Field', name):
                current = frappe.get_doc('Custom Field', name)
                if any((current.get(k) or '') != (field.get(k) or '') for k in ['fieldtype', 'options', 'read_only', 'no_copy', 'unique']):
                    frappe.throw('El campo existente requiere revisión: '+name)
            else:
                frappe.get_doc(field).insert()
            after = field['fieldname']
    servers, clients = specs()
    for spec in servers + clients:
        if frappe.db.exists(spec['doctype'], spec['name']):
            current = frappe.get_doc(spec['doctype'], spec['name'])
            keys = ['script', 'script_type', 'reference_doctype', 'doctype_event', 'api_method', 'allow_guest', 'disabled'] if spec['doctype']=='Server Script' else ['script', 'dt', 'view']
            if any((current.get(k) or '') != (spec.get(k) or '') for k in keys):
                frappe.throw('El script fue modificado; concilie los cambios antes de instalar: '+spec['name'])
        else:
            current = frappe.get_doc(spec).insert()
        if spec['doctype']=='Client Script' and frappe.utils.cint(enable_ui) and not current.enabled:
            current.enabled = 1
            current.save()
    frappe.clear_cache()
    return {'server_scripts': len(servers), 'client_scripts': len(clients), 'ui_enabled_requested': bool(frappe.utils.cint(enable_ui))}
