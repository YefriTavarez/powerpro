"""Explicit, reversible installation. Deliberately not in patches.txt.

Install and enable are separate actions. No existing Salary Slip is saved.
"""

import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import getdate

from powerpro.payroll_rules.monthly_settlement import MANAGED
from powerpro.payroll_rules.employer_contributions import DEDICATED_MODE

NEW_FORMULAS = {
    "BAM": "pp_monthly_salary",
    "AFP": "pp_afp_due",
    "ARS": "pp_ars_due",
    "MIMP": "pp_taxable_earnings",
    "BIMP": "max(0, MIMP - pp_afp_total - pp_ars_total - pp_prior_dp - DP)",
    "ABIMP": "BIMP * 12",
    "ISRM": "pp_isr(DP)",
}
FIELDS = ("formula", "condition", "amount_based_on_formula", "depends_on_payment_days")


def _state(row):
    return {k: row.get(k) for k in FIELDS}


def _replacement(abbr, original):
    result = dict(original)
    result["formula"] = f'({NEW_FORMULAS[abbr]}) if pp_monthly_enabled else ({original["formula"] or "0"})'
    result["amount_based_on_formula"] = 1
    if abbr in ("AFP", "ARS", "ISRM"):
        result["condition"] = f'pp_monthly_close if pp_monthly_enabled else ({original["condition"] or "True"})'
    return result


def _clear():
    for dt in ("DGII Payroll Settings", "Salary Slip", "Salary Component", "Salary Structure"):
        frappe.clear_cache(doctype=dt)


def execute(structures=None):
    frappe.only_for("System Manager")
    structures = structures or ["General Quincenal"]
    if isinstance(structures, str):
        structures = json.loads(structures)
    # Inspect all targets before doing DDL or writing configuration.
    documents = [frappe.get_doc("Salary Structure", name) for name in structures]
    for doc in documents:
        if doc.docstatus != 1 or doc.is_active != "Yes":
            frappe.throw("Estructura no confirmada/activa: " + doc.name)
        abbrs = [r.abbr for r in doc.deductions if r.abbr in MANAGED]
        if set(abbrs) != MANAGED or len(abbrs) != len(MANAGED):
            frappe.throw("La estructura debe contener exactamente una fila de cada componente mensual: " + doc.name)
    create_custom_fields({
        "DGII Payroll Settings": [
            {"fieldname": "monthly_settlement_section", "fieldtype": "Section Break", "label": "Acumulado mensual"},
            {"fieldname": "enable_monthly_settlement", "fieldtype": "Check", "label": "Activar acumulado mensual", "default": "0", "insert_after": "monthly_settlement_section"},
            {"fieldname": "monthly_settlement_from_date", "fieldtype": "Date", "label": "Acumulado vigente desde", "insert_after": "enable_monthly_settlement"},
            {"fieldname": "monthly_settlement_backup", "fieldtype": "Code", "options": "JSON", "label": "Configuración anterior del acumulado", "hidden": 1, "read_only": 1, "insert_after": "monthly_settlement_from_date"},
        ],
        "Salary Slip": [
            {"fieldname": "monthly_settlement_tab", "fieldtype": "Tab Break", "label": "Acumulado mensual", "depends_on": "eval:!!doc.monthly_settlement_snapshot", "insert_after": "employer_contributions"},
            {"fieldname": "monthly_settlement_view", "fieldtype": "HTML", "label": "Detalle del acumulado", "insert_after": "monthly_settlement_tab"},
            {"fieldname": "monthly_settlement_snapshot", "fieldtype": "Code", "options": "JSON", "label": "Evidencia del cálculo mensual", "read_only": 1, "hidden": 1, "allow_on_submit": 0, "insert_after": "monthly_settlement_view"},
        ],
    }, update=True)
    _clear()
    settings = frappe.get_single("DGII Payroll Settings")
    backup = json.loads(settings.get("monthly_settlement_backup") or "{}")
    if backup and set(backup["structures"]) != set(structures):
        frappe.throw("La instalación ya tiene otro alcance. Revertir antes de cambiar las estructuras.")
    if not backup:
        components = {}
        rows = {}
        for doc in documents:
            rows[doc.name] = {}
            for row in doc.deductions:
                if row.abbr in MANAGED:
                    rows[doc.name][row.name] = {"abbr": row.abbr, "component": row.salary_component, **_state(row)}
                    component = frappe.get_doc("Salary Component", row.salary_component)
                    components[component.name] = {"abbr": row.abbr, **_state(component)}
        backup = {"version": 1, "components": components, "structures": rows,
                  "settings": {"enabled": settings.get("enable_monthly_settlement") or 0,
                               "from_date": str(settings.get("monthly_settlement_from_date")) if settings.get("monthly_settlement_from_date") else None}}
        settings.monthly_settlement_backup = json.dumps(backup, default=str)
        settings.save(ignore_permissions=True)
        # Persist restoration evidence before later data updates; DDL already commits.
        frappe.db.commit()
    _apply(backup, restoring=False)
    _clear()
    return preview()


def _apply(backup, restoring):
    for name, original in backup["components"].items():
        doc = frappe.get_doc("Salary Component", name)
        replacement = _replacement(original["abbr"], original)
        expected = {k: replacement[k] for k in FIELDS}
        old = {k: original[k] for k in FIELDS}
        if _state(doc) not in (old, expected):
            frappe.throw("El componente fue modificado fuera del instalador: " + name)
        target = old if restoring else expected
        if _state(doc) != target:
            doc.update(target)
            doc.save(ignore_permissions=True)
    for name, originals in backup["structures"].items():
        doc = frappe.get_doc("Salary Structure", name)
        by_name = {r.name: r for r in doc.deductions}
        changed = False
        for row_name, original in originals.items():
            if row_name not in by_name:
                frappe.throw("La fila salarial original ya no existe: " + row_name)
            row = by_name[row_name]
            replacement = _replacement(original["abbr"], original)
            expected, old = ({k: source[k] for k in FIELDS} for source in (replacement, original))
            if _state(row) not in (old, expected):
                frappe.throw("La fila salarial fue modificada fuera del instalador: " + row_name)
            target = old if restoring else expected
            if _state(row) != target:
                row.update(target)
                changed = True
        if changed:
            doc.flags.ignore_validate_update_after_submit = True
            doc.save(ignore_permissions=True)


def enable(from_date="2026-09-01"):
    frappe.only_for("System Manager")
    settings = frappe.get_single("DGII Payroll Settings")
    if not settings.monthly_settlement_backup or settings.employer_contribution_mode != DEDICATED_MODE:
        frappe.throw("Instale el acumulado y active la tabla patronal dedicada antes de habilitarlo.")
    if getdate(from_date).day != 1:
        frappe.throw("La vigencia debe comenzar el primer día de un mes.")
    settings.monthly_settlement_from_date = from_date
    settings.enable_monthly_settlement = 1
    settings.save(ignore_permissions=True)
    _clear()
    return preview()


def rollback():
    frappe.only_for("System Manager")
    settings = frappe.get_single("DGII Payroll Settings")
    backup = json.loads(settings.get("monthly_settlement_backup") or "{}")
    if not backup:
        return preview()
    _apply(backup, restoring=True)
    settings.enable_monthly_settlement = backup["settings"]["enabled"]
    settings.monthly_settlement_from_date = backup["settings"]["from_date"]
    settings.save(ignore_permissions=True)
    _clear()
    return preview()


def preview():
    settings = frappe.get_single("DGII Payroll Settings")
    backup = json.loads(settings.get("monthly_settlement_backup") or "{}")
    return {"enabled": settings.get("enable_monthly_settlement") or 0,
            "from_date": settings.get("monthly_settlement_from_date"),
            "structures": list(backup.get("structures", {})),
            "original_configuration_preserved": bool(backup), "existing_slips_changed": 0}
