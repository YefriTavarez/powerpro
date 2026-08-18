# Copyright (c) 2026, Yefri Tavarez and Contributors
# For license information, please see license.txt

"""Sincroniza el componente de ISR y sus filas en las estructuras salariales
con la escala DGII 2026 (Art. 296 del Código Tributario 11-92).

Reglas implementadas:

* La retención se calcula a partir de `ABIMP` (Base Imponible Anual),
  que en estas estructuras viene de:
        MIMP  = BAM + COM + (HRE + HN + HE) + VAC + BVA + INC + BNF
        BIMP  = MIMP - AFP - ARS - DP
        ABIMP = BIMP * 12

* Escala anual DGII 2026 (legalmente igual desde 2017):

        Hasta RD$ 416,220.00         -> Exento
        416,220.01 -  624,329.00     -> 15% del excedente sobre 416,220
        624,329.01 -  867,123.00     -> 31,216 + 20% del excedente sobre 624,329
        Más de 867,123.01            -> 79,776 + 25% del excedente sobre 867,123

* La retención mensual = ISR anual / 12.

* La retención SOLO se ejecuta en el cierre de mes:
        - Nóminas `Monthly`: siempre.
        - Nóminas `Bimonthly` (quincenal): únicamente en la
          segunda quincena (`mid_month_start = True`).
  Esto replica el comportamiento ya existente para AFP, ARS y Dependientes.
"""

import frappe


ISR_FORMULA = (
	"("
	"(ABIMP - 416220.01) * 0.15 if 416220.01 <= ABIMP <= 624329 "
	"else (ABIMP - 624329.01) * 0.20 + 31216 if 624329.01 <= ABIMP <= 867123 "
	"else (ABIMP - 867123.01) * 0.25 + 79776 if 867123.01 <= ABIMP "
	"else 0"
	") / 12"
)

ISR_CONDITION = 'mid_month_start or payroll_frequency == "Monthly"'

STRUCTURES = ("General Quincenal", "General Mensual")
ISR_COMPONENT_NAMES = ("Impuesto Sobre la Renta Mensual", "ISR")


def execute():
	component_names = get_existing_isr_component_names()
	if not component_names:
		frappe.throw(
			"No se encontró un Salary Component de ISR compatible. "
			f"Nombres esperados: {', '.join(ISR_COMPONENT_NAMES)}"
		)

	for component_name in component_names:
		update_isr_salary_component(component_name)

	updated_rows = 0
	for structure_name in STRUCTURES:
		updated_rows += update_salary_structure_isr_rows(structure_name, component_names)

	if not updated_rows:
		frappe.throw(
			"No se encontró ninguna fila de ISR en las estructuras salariales "
			f"esperadas: {', '.join(STRUCTURES)}"
		)

	frappe.clear_cache(doctype="Salary Component")
	frappe.clear_cache(doctype="Salary Structure")
	print(
		"[setup_dgii_isr_2026] "
		f"Componentes sincronizados: {', '.join(component_names)}; "
		f"filas actualizadas: {updated_rows}."
	)


def get_existing_isr_component_names():
	return tuple(
		name for name in ISR_COMPONENT_NAMES if frappe.db.exists("Salary Component", name)
	)


def update_isr_salary_component(component_name):
	doc = frappe.get_doc("Salary Component", component_name)
	doc.update({
		"amount_based_on_formula": 1,
		"formula": ISR_FORMULA,
		"condition": ISR_CONDITION,
		"variable_based_on_taxable_salary": 0,
		"is_income_tax_component": 1,
		"depends_on_payment_days": 0,
		"statistical_component": 0,
		"do_not_include_in_total": 0,
	})
	doc.flags.ignore_permissions = True
	doc.save()

	print(
		f"[setup_dgii_isr_2026] Salary Component '{component_name}' "
		"sincronizado con escala DGII 2026."
	)


def update_salary_structure_isr_rows(structure_name, component_names):
	if not frappe.db.exists("Salary Structure", structure_name):
		print(
			f"[setup_dgii_isr_2026] Salary Structure '{structure_name}' "
			"no existe; se omite."
		)
		return 0

	row_names = frappe.get_all(
		"Salary Detail",
		filters={
			"parent": structure_name,
			"parenttype": "Salary Structure",
			"parentfield": "deductions",
			"salary_component": ["in", component_names],
		},
		pluck="name",
	)

	if not row_names:
		print(
			f"[setup_dgii_isr_2026] '{structure_name}' no contiene fila ISR; "
			"se omite."
		)
		return 0

	for row_name in row_names:
		frappe.db.set_value(
			"Salary Detail",
			row_name,
			{
				"amount_based_on_formula": 1,
				"formula": ISR_FORMULA,
				"condition": ISR_CONDITION,
				"variable_based_on_taxable_salary": 0,
			},
			update_modified=False,
		)

	print(
		f"[setup_dgii_isr_2026] {len(row_names)} fila(s) ISR sincronizada(s) "
		f"en Salary Structure '{structure_name}'."
	)
	return len(row_names)
