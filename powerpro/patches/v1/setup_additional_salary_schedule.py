"""Opt-in metadata only: no adoption of live salaries and no payroll writes."""
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from powerpro.payroll_rules.additional_salary_schedule import MODES


def execute():
    create_custom_fields({
        "Additional Salary": [
            dict(fieldname="pp_recurring_distribution", label="Aplicación en Nómina", fieldtype="Select",
                 options="\n" + "\n".join(MODES), insert_after="is_recurring", allow_on_submit=1,
                 depends_on="eval:doc.is_recurring", print_hide=0,
                 description="Con una opción seleccionada, Importe es la base mensual. Sin selección se conserva el comportamiento anterior: importe completo en cada nómina aplicable. Las reglas de prorrateo del componente no cambian."),
            dict(fieldname="pp_recurring_distribution_from", label="Aplicar desde el Mes", fieldtype="Date",
                 insert_after="pp_recurring_distribution", allow_on_submit=1, no_copy=1,
                 depends_on="eval:doc.is_recurring && doc.pp_recurring_distribution",
                 mandatory_depends_on="eval:doc.is_recurring && doc.pp_recurring_distribution",
                 description="Primer día del mes desde el que aplica la nueva selección. No modifica nóminas validadas."),
        ],
        "Salary Slip": [dict(fieldname="pp_recurring_salary_snapshot", label="Aplicación de Salarios Adicionales Recurrentes",
                             fieldtype="Long Text", hidden=1, read_only=1, no_copy=1)],
    }, update=False)
