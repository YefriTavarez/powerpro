# Editable document-event rules. Python capabilities are not RPC endpoints.
def run(doc):
    def fail(message):
        frappe.throw(_(str(message)), title=_('Complementos de nómina'))
    old = doc.get_doc_before_save()
    if old and frappe.db.count('Employee Supplement Revision'):
        for key in ('company', 'currency', 'effective_from', 'second_quincena_day', 'amount_precision'):
            if str(doc.get(key) or '') != str(old.get(key) or ''):
                fail('La política con historial no se puede reinterpretar. Conserve empresa, moneda, vigencia y calendario.')
        mapping = lambda d: sorted(((r.source_field, r.salary_component) for r in d.mappings))
        if mapping(doc) != mapping(old):
            fail('No cambie el mapeo después de iniciar el historial de complementos.')
        classify = lambda d: {(r.additional_salary, r.treatment, r.source_field or '') for r in d.existing_salaries}
        if not classify(old).issubset(classify(doc)):
            fail('No quite ni cambie asociaciones existentes después de iniciar el historial.')
    if not doc.enabled:
        return
    if not doc.company or not doc.currency or (not doc.effective_from):
        fail('Defina empresa, moneda y fecha de inicio antes de habilitar los complementos.')
    if frappe.utils.cint(doc.second_quincena_day) not in (15, 16) or frappe.utils.cint(doc.amount_precision) not in (2, 4):
        fail('Calendario o precisión inválidos.')
    if frappe.utils.getdate(doc.effective_from).day not in (1, frappe.utils.cint(doc.second_quincena_day)):
        fail('La fecha de inicio debe coincidir con el comienzo de una quincena.')
    mappings = {r.source_field: r.salary_component for r in doc.mappings}
    if set(mappings) != set(('incentivo_especial', 'asignacion_transporte', 'asignacion_combustible', 'asignacion_mantenimiento_vehiculo')) or len(doc.mappings) != len(('incentivo_especial', 'asignacion_transporte', 'asignacion_combustible', 'asignacion_mantenimiento_vehiculo')):
        fail('Configure una fila para cada uno de los cuatro campos de Employee.')
    if len(set(mappings.values())) != len(mappings) or not all(mappings.values()):
        fail('Cada complemento requiere un componente de ingreso distinto.')
    for field, name in mappings.items():
        meta = frappe.get_meta('Employee').get_field(field)
        if not meta or meta.fieldtype != 'Currency':
            fail(f'Employee.{field} debe existir como Currency.')
        component = frappe.get_doc('Salary Component', name)
        if component.type != 'Earning' or any(component.get(k) for k in ('disabled', 'depends_on_payment_days', 'statistical_component', 'do_not_include_in_total', 'do_not_include_in_accounts', 'variable_based_on_taxable_salary', 'is_flexible_benefit')):
            fail(f'{name}: use un ingreso habilitado, pagable y sin prorrateo por días.')
    seen = set()
    for row in doc.existing_salaries:
        if row.additional_salary in seen:
            fail('Un Additional Salary solo puede tener una clasificación.')
        seen.add(row.additional_salary)
        salary = frappe.get_doc('Additional Salary', row.additional_salary, for_update=True)
        if salary.company != doc.company or salary.currency != doc.currency or salary.type != 'Earning':
            fail(f'{salary.name}: empresa, moneda o tipo incompatible.')
        if salary.get('pp_supplement_key') or salary.overwrite_salary_structure_amount:
            fail(f'{salary.name}: no se puede asociar un automático ni un reemplazo de estructura.')
        if salary.docstatus != 1 or salary.disabled:
            fail(f'{salary.name}: debe estar confirmado y habilitado para conciliarlo.')
        if row.treatment == 'Coverage':
            if mappings.get(row.source_field) != salary.salary_component:
                fail(f'{salary.name}: el componente no corresponde al campo de origen.')
        elif row.treatment != 'Independent':
            fail('Seleccione Coverage o Independent para cada adicional existente.')
    rows = frappe.get_all('Additional Salary', filters={'company': doc.company, 'docstatus': 1, 'disabled': 0, 'salary_component': ['in', list(mappings.values())]}, fields=['name', 'employee', 'company', 'currency', 'salary_component', 'type', 'amount', 'docstatus', 'disabled', 'is_recurring', 'from_date', 'to_date', 'payroll_date', 'overwrite_salary_structure_amount', 'pp_supplement_key', 'pp_supplement_field', 'pp_supplement_start', 'pp_supplement_end', 'pp_supplement_monthly', 'pp_supplement_treatment'])
    for row in rows:
        relevant = row.is_recurring and row.to_date and (frappe.utils.getdate(row.to_date) >= frappe.utils.getdate(doc.effective_from)) or (not row.is_recurring and row.payroll_date and (frappe.utils.getdate(row.payroll_date) >= frappe.utils.getdate(doc.effective_from)))
        if relevant and (not row.pp_supplement_key) and (row.name not in seen) and (row.pp_supplement_treatment != 'Independent'):
            fail(f'Concilie {row.name} como cobertura o pago independiente antes de habilitar.')
    if not frappe.db.count('Employee Supplement Revision') and frappe.db.exists('Salary Slip', {'company': doc.company, 'docstatus': ['<', 2], 'end_date': ['>=', doc.effective_from]}):
        fail('El inicio se superpone con recibos existentes. Elija una fecha posterior para la transición.')

run(doc)
