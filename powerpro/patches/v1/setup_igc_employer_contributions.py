# Copyright (c) 2026, PowerPro contributors
# For license information, please see license.txt

"""Configure balanced Dominican employer payroll contributions for IGC.

The patch is deliberately idempotent and performs no historical Salary Slip
recalculation. Each employer obligation is represented by an excluded earning
(debit employer expense) and an excluded deduction (credit the liability), so
employee gross pay, deductions, and net pay remain unchanged.
"""

import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


COMPANY = "INDUSTRIA GRÁFICA DEL CARIBE"
SALARY_STRUCTURE = "General Quincenal"
TSS_PAYABLE = "213108 - TESORERIA DE LA SEGURIDAD SOCIAL POR PAGAR - IGC"
INFOTEP_PAYABLE = "213109 - INFOTEP POR PAGAR - IGC"
TSS_EXPENSE = "612101 - TSS PROPORCION EMPLEADOR - IGC"
SRL_EXPENSE = "612201 - APORTE RIESGOS LABORALES (SRL) - IGC"
INFOTEP_EXPENSE = "612401 - INFOTEP - IGC"

MONTHLY_CONDITION = 'mid_month_start or payroll_frequency == "Monthly"'
FORMULAS = {
	"AFP": "base * 0.0710",
	"ARS": "base * 0.0709",
	"INFOTEP": "(base + COM) * (infotep_employer_rate / 100)",
	"SRL": (
		"(base + COM + VAC if base + COM + VAC <= srl_ceiling else srl_ceiling) "
		"* (srl_employer_rate / 100)"
	),
}

COMPONENTS = (
	{
		"name": "Gasto AFP Empleador",
		"abbr": "GAFP",
		"type": "Earning",
		"formula": FORMULAS["AFP"],
		"account": TSS_EXPENSE,
		"table": "earnings",
	},
	{
		"name": "AFP Empleador",
		"abbr": "AEAFP",
		"type": "Deduction",
		"formula": FORMULAS["AFP"],
		"account": TSS_PAYABLE,
		"table": "deductions",
	},
	{
		"name": "Gasto ARS Empleador",
		"abbr": "GARS",
		"type": "Earning",
		"formula": FORMULAS["ARS"],
		"account": TSS_EXPENSE,
		"table": "earnings",
	},
	{
		"name": "ARS Empleador",
		"abbr": "AEARS",
		"type": "Deduction",
		"formula": FORMULAS["ARS"],
		"account": TSS_PAYABLE,
		"table": "deductions",
	},
	{
		"name": "Gasto INFOTEP Empleador",
		"abbr": "GINF",
		"type": "Earning",
		"formula": FORMULAS["INFOTEP"],
		"account": INFOTEP_EXPENSE,
		"table": "earnings",
	},
	{
		"name": "INFOTEP Empleador",
		"abbr": "INFEM",
		"type": "Deduction",
		"formula": FORMULAS["INFOTEP"],
		"account": INFOTEP_PAYABLE,
		"table": "deductions",
	},
	{
		"name": "Gasto SRL Empleador",
		"abbr": "GSRL",
		"type": "Earning",
		"formula": FORMULAS["SRL"],
		"account": SRL_EXPENSE,
		"table": "earnings",
	},
	{
		"name": "SRL Empleador",
		"abbr": "SRLEM",
		"type": "Deduction",
		"formula": FORMULAS["SRL"],
		"account": TSS_PAYABLE,
		"table": "deductions",
	},
)

NEW_COMPONENT_NAMES = {
	"Gasto AFP Empleador",
	"Gasto ARS Empleador",
	"Gasto INFOTEP Empleador",
	"INFOTEP Empleador",
	"Gasto SRL Empleador",
	"SRL Empleador",
}


def preview():
	"""Return current state and the exact intended configuration without writes."""
	_validate_dependencies()
	return {
		"company": COMPANY,
		"salary_structure": SALARY_STRUCTURE,
		"settings": _current_settings(),
		"components": [_component_state(spec["name"]) for spec in COMPONENTS],
		"intended_components": list(COMPONENTS),
		"historical_salary_slips_changed": 0,
	}


def execute():
	_validate_dependencies()
	_create_salary_slip_fields()
	_set_default_rates()

	for spec in COMPONENTS:
		_upsert_component(spec)

	_upsert_structure_rows()
	frappe.clear_cache(doctype="Salary Component")
	frappe.clear_cache(doctype="Salary Structure")
	frappe.clear_cache(doctype="Salary Slip")

	print("[setup_igc_employer_contributions] " + json.dumps(_after_state(), default=str, sort_keys=True))


def rollback():
	"""Stop future calculation while preserving any historical references."""
	if frappe.db.exists("Salary Structure", SALARY_STRUCTURE):
		structure = frappe.get_doc("Salary Structure", SALARY_STRUCTURE)
		for table in ("earnings", "deductions"):
			structure.set(
				table,
				[row for row in structure.get(table) if row.salary_component not in NEW_COMPONENT_NAMES],
			)
		structure.flags.ignore_validate_update_after_submit = True
		structure.save(ignore_permissions=True)

	for name in NEW_COMPONENT_NAMES:
		if frappe.db.exists("Salary Component", name):
			frappe.db.set_value("Salary Component", name, "disabled", 1)

	for name in ("AFP Empleador", "ARS Empleador"):
		if frappe.db.exists("Salary Component", name):
			doc = frappe.get_doc("Salary Component", name)
			_set_company_account(doc, TSS_EXPENSE)
			doc.save(ignore_permissions=True)

	frappe.clear_cache(doctype="Salary Component")
	frappe.clear_cache(doctype="Salary Structure")
	print("[setup_igc_employer_contributions] Future employer contribution rows disabled.")


def _validate_dependencies():
	missing = []
	if not frappe.db.exists("Company", COMPANY):
		missing.append(f"Company: {COMPANY}")
	if not frappe.db.exists("Salary Structure", SALARY_STRUCTURE):
		missing.append(f"Salary Structure: {SALARY_STRUCTURE}")

	for account in (TSS_PAYABLE, INFOTEP_PAYABLE, TSS_EXPENSE, SRL_EXPENSE, INFOTEP_EXPENSE):
		if not frappe.db.exists("Account", {"name": account, "company": COMPANY, "disabled": 0}):
			missing.append(f"Account: {account}")

	if missing:
		frappe.throw("Missing employer-contribution dependencies:\n- " + "\n- ".join(missing))


def _create_salary_slip_fields():
	create_custom_fields({
		"Salary Slip": [
			{
				"fieldname": "infotep_employer_rate",
				"label": "INFOTEP Employer Rate",
				"fieldtype": "Percent",
				"insert_after": "pension_fund_provider",
				"default": "1",
				"precision": "2",
				"read_only": 1,
				"hidden": 1,
				"non_negative": 1,
			},
			{
				"fieldname": "srl_employer_rate",
				"label": "SRL Employer Rate",
				"fieldtype": "Percent",
				"insert_after": "infotep_employer_rate",
				"default": "1.2",
				"precision": "2",
				"read_only": 1,
				"hidden": 1,
				"non_negative": 1,
			},
			{
				"fieldname": "srl_ceiling",
				"label": "SRL Cotizable Ceiling",
				"fieldtype": "Currency",
				"insert_after": "srl_employer_rate",
				"precision": "2",
				"read_only": 1,
				"hidden": 1,
				"non_negative": 1,
			},
		]
	}, ignore_validate=True, update=True)


def _set_default_rates():
	settings = frappe.get_single("DGII Payroll Settings")
	changed = False
	if not settings.infotep_employer_rate:
		settings.infotep_employer_rate = 1.0
		changed = True
	if not settings.srl_employer_rate:
		settings.srl_employer_rate = 1.2
		changed = True
	if changed:
		settings.save(ignore_permissions=True)


def _upsert_component(spec):
	if frappe.db.exists("Salary Component", spec["name"]):
		doc = frappe.get_doc("Salary Component", spec["name"])
	else:
		doc = frappe.new_doc("Salary Component")
		doc.salary_component = spec["name"]

	values = {
		"salary_component_abbr": spec["abbr"],
		"type": spec["type"],
		"disabled": 0,
		"amount_based_on_formula": 1,
		"formula": spec["formula"],
		"condition": MONTHLY_CONDITION,
		"depends_on_payment_days": 1,
		"variable_based_on_taxable_salary": 0,
		"is_tax_applicable": 0,
		"statistical_component": 0,
		"do_not_include_in_total": 1,
		"do_not_include_in_accounts": 0,
	}
	account_matches = [
		row.account for row in doc.accounts if row.company == COMPANY
	] == [spec["account"]]
	if not doc.is_new() and account_matches and all(doc.get(key) == value for key, value in values.items()):
		return

	doc.update(values)
	_set_company_account(doc, spec["account"])
	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)


def _set_company_account(doc, account):
	rows = [row.as_dict() for row in doc.accounts if row.company != COMPANY]
	rows.append({"company": COMPANY, "account": account})
	doc.set("accounts", rows)


def _upsert_structure_rows():
	structure = frappe.get_doc("Salary Structure", SALARY_STRUCTURE)
	wanted = {spec["name"]: spec for spec in COMPONENTS}
	changed = False

	for table in ("earnings", "deductions"):
		for component_name, spec in wanted.items():
			if spec["table"] != table:
				continue
			row = next(
				(item for item in structure.get(table) if item.salary_component == component_name),
				None,
			)
			if row is None:
				row = structure.append(table, {"salary_component": component_name})
				changed = True
			values = {
				"abbr": spec["abbr"],
				"amount_based_on_formula": 1,
				"formula": spec["formula"],
				"condition": MONTHLY_CONDITION,
				"depends_on_payment_days": 1,
				"variable_based_on_taxable_salary": 0,
				"statistical_component": 0,
				"do_not_include_in_total": 1,
				"do_not_include_in_accounts": 0,
			}
			if any(row.get(key) != value for key, value in values.items()):
				row.update(values)
				changed = True

	if changed:
		structure.flags.ignore_validate_update_after_submit = True
		structure.save(ignore_permissions=True)


def _component_state(name):
	if not frappe.db.exists("Salary Component", name):
		return {"name": name, "exists": False}
	doc = frappe.get_doc("Salary Component", name)
	return {
		"name": name,
		"exists": True,
		"abbr": doc.salary_component_abbr,
		"type": doc.type,
		"disabled": doc.disabled,
		"formula": doc.formula,
		"condition": doc.condition,
		"do_not_include_in_total": doc.do_not_include_in_total,
		"do_not_include_in_accounts": doc.do_not_include_in_accounts,
		"accounts": [{"company": row.company, "account": row.account} for row in doc.accounts],
	}


def _current_settings():
	settings = frappe.get_single("DGII Payroll Settings")
	return {
		"infotep_employer_rate": settings.get("infotep_employer_rate"),
		"srl_employer_rate": settings.get("srl_employer_rate"),
	}


def _after_state():
	structure = frappe.get_doc("Salary Structure", SALARY_STRUCTURE)
	return {
		"settings": _current_settings(),
		"components": [_component_state(spec["name"]) for spec in COMPONENTS],
		"structure_rows": [
			{
				"table": table,
				"salary_component": row.salary_component,
				"formula": row.formula,
				"condition": row.condition,
			}
			for table in ("earnings", "deductions")
			for row in structure.get(table)
			if row.salary_component in {spec["name"] for spec in COMPONENTS}
		],
		"historical_salary_slips_changed": 0,
	}
