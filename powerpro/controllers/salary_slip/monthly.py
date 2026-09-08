"""Frappe adapter for the monthly settlement; calculations never persist other slips."""

import copy
import json
from collections import defaultdict

import frappe
from frappe.utils import getdate

from powerpro.payroll_rules.monthly_settlement import (
    MANAGED, calculate, money, month_bounds, period_issues, taxable_amounts,
)
from powerpro.payroll_rules.employer_contributions import DEDICATED_MODE


def settings_for(doc):
    if getattr(doc, "_pp_force_legacy", False):
        return None
    settings = frappe.get_single("DGII Payroll Settings")
    if not settings.get("enable_monthly_settlement") or not doc.end_date:
        return None
    if not settings.get("monthly_settlement_from_date"):
        frappe.throw("El acumulado mensual requiere fecha de vigencia.")
    if getdate(doc.end_date) < getdate(settings.monthly_settlement_from_date):
        return None
    selected = json.loads(settings.get("monthly_settlement_backup") or "{}").get("structures", {})
    return settings if doc.salary_structure in selected else None


def lock_employee(doc):
    # A stable existing row serializes all payroll submissions/cancellations for this employee.
    # Locking is taken before HRMS validation, and retained until transaction completion.
    if doc.employee:
        frappe.db.sql("select name from `tabEmployee` where name=%s for update", doc.employee)
        doc._pp_monthly_locked = True


def read_history(doc):
    first, last = month_bounds(doc.end_date)
    lock = " for update" if getattr(doc, "_pp_monthly_locked", False) else ""
    slips = frappe.db.sql(
        """select name, start_date, end_date, docstatus, currency, payroll_frequency,
                  employer_contribution_mode, monthly_settlement_snapshot
           from `tabSalary Slip` where employee=%s and company=%s
           and start_date <= %s and end_date >= %s and docstatus in (0,1)
           and name != %s order by start_date, name""" + lock,
        (doc.employee, doc.company, last, first, doc.name or ""), as_dict=True,
    )
    prior = [s for s in slips if s.docstatus == 1 and getdate(s.end_date) < getdate(doc.start_date)]
    earnings, deductions, employer = defaultdict(money), defaultdict(money), defaultdict(money)
    sources = []
    if prior:
        names = tuple(s.name for s in prior)
        details = frappe.db.sql(
            """select parent, parentfield, salary_component, abbr, amount, is_tax_applicable,
                      do_not_include_in_total, additional_salary
               from `tabSalary Detail` where parenttype='Salary Slip' and parent in %s""" + lock,
            (names,), as_dict=True,
        )
        contributions = frappe.db.sql(
            """select parent, contribution_code, amount from `tabEmployer Contribution Detail`
               where parenttype='Salary Slip' and parent in %s""" + lock,
            (names,), as_dict=True,
        )
        for row in details:
            if row.parentfield == "earnings" and not row.do_not_include_in_total:
                earnings[row.abbr] += money(row.amount)
            elif row.parentfield == "deductions":
                deductions[row.abbr] += money(row.amount)
        for row in contributions:
            employer[row.contribution_code] += money(row.amount)
        for slip in prior:
            sources.append({"name": slip.name, "start_date": str(slip.start_date),
                            "end_date": str(slip.end_date),
                            "rows": [dict(r) for r in details if r.parent == slip.name],
                            "employer": [dict(r) for r in contributions if r.parent == slip.name]})
    return slips, dict(earnings), dict(deductions), dict(employer), sources


def prepare(doc):
    doc._pp_monthly = None
    settings = settings_for(doc)
    # Always work on a private copy; never mutate Frappe's shared cached structure.
    doc.set_salary_structure_doc()
    doc._salary_structure_doc = copy.deepcopy(doc._salary_structure_doc)
    original_flags = {r.salary_component: r.depends_on_payment_days for r in doc._salary_structure_doc.deductions}
    for row in doc.deductions:
        if row.abbr in MANAGED and row.salary_component in original_flags:
            row.depends_on_payment_days = original_flags[row.salary_component]
    if not settings:
        if doc.meta.has_field("monthly_settlement_snapshot"):
            doc.monthly_settlement_snapshot = None
        return
    if settings.employer_contribution_mode != DEDICATED_MODE:
        frappe.throw("El acumulado mensual requiere la tabla de aportes patronales dedicada.")
    doc.employer_contribution_mode = DEDICATED_MODE
    history, previous, deductions, employer, sources = read_history(doc)
    current = defaultdict(money)
    issues = period_issues(doc.as_dict(), history, doc.joining_date, doc.relieving_date)
    if doc.currency != "DOP" or any(s.currency != doc.currency for s in history if s.docstatus == 1):
        issues.append("El acumulado requiere recibos en DOP con moneda consistente.")
    for row in doc.earnings:
        if row.do_not_include_in_total:
            continue
        current[row.abbr] += money(row.amount)
    current_taxable = taxable_amounts(doc.earnings)
    previous_taxable = taxable_amounts(
        row for source in sources for row in source["rows"] if row["parentfield"] == "earnings"
    )
    for slip in history:
        if slip.docstatus == 1 and slip.employer_contribution_mode != DEDICATED_MODE:
            issues.append("El mes contiene aportes patronales en modo anterior: " + slip.name)
    first, last = month_bounds(doc.end_date)
    close = getdate(doc.end_date) == last
    for row in doc._salary_structure_doc.deductions:
        if row.abbr in MANAGED:
            row.depends_on_payment_days = 0
    for row in doc.deductions:
        if row.abbr in MANAGED:
            row.depends_on_payment_days = 0
    # Rebuild managed deductions, including zero balances and first-half recalculations.
    # Additional Salary rows are added again by HRMS and checked against the obligation.
    doc.set("deductions", [row for row in doc.deductions if row.abbr not in ("AFP", "ARS", "ISRM")])
    doc._pp_monthly = {
        "current": dict(current), "previous": previous, "previous_deductions": deductions,
        "current_taxable": current_taxable, "previous_taxable": previous_taxable,
        "previous_employer": employer, "sources": sources, "close": close,
        "period": {"from": str(first), "to": str(last)}, "issues": issues,
        "rates": {"employee_afp_rate": settings.pension_fund_provider,
                  "employee_ars_rate": settings.health_insurance_rate,
                  "infotep_rate": settings.infotep_employer_rate, "srl_rate": settings.srl_employer_rate},
    }
    doc._pp_monthly["calculation"] = compute(doc)


def compute(doc, dependents=0):
    ctx = doc._pp_monthly
    return calculate(ctx["current"], ctx["previous"], ctx["previous_deductions"],
                     ctx["previous_employer"], str(doc.end_date), dependents,
                     current_taxable=ctx["current_taxable"], previous_taxable=ctx["previous_taxable"],
                     **ctx["rates"])


def formula_data(doc):
    ctx = getattr(doc, "_pp_monthly", None)
    if not ctx:
        return {"pp_monthly_enabled": False, "pp_monthly_close": False}
    result = ctx["calculation"]
    return {
        "pp_monthly_enabled": True, "pp_monthly_close": ctx["close"],
        "pp_monthly_salary": float(result["salary"]),
        "pp_taxable_earnings": float(result["taxable_earnings"]),
        "pp_afp_total": float(result["employee"]["AFP"]["total"]),
        "pp_ars_total": float(result["employee"]["ARS"]["total"]),
        "pp_afp_due": float(result["employee"]["AFP"]["amount"]),
        "pp_ars_due": float(result["employee"]["ARS"]["amount"]),
        "pp_prior_dp": float(money(ctx["previous_deductions"].get("DP"))),
    }


def evaluate_isr(doc, dependents):
    result = compute(doc, dependents)
    return float(result["employee"]["ISRM"]["amount"])


def finish(doc):
    ctx = getattr(doc, "_pp_monthly", None)
    if not ctx:
        return
    dp = sum((money(r.amount) for r in doc.deductions if r.abbr == "DP"), money())
    result = compute(doc, dp)
    result.update({"sources": ctx["sources"], "period": ctx["period"], "close": ctx["close"],
                   "issues": list(dict.fromkeys(ctx["issues"] + (result["issues"] if ctx["close"] else [])))})
    expected = {code: float(row["amount"]) if ctx["close"] else 0 for code, row in result["employee"].items()}
    for code, amount in expected.items():
        actual = sum(money(r.amount) for r in doc.deductions if r.abbr == code)
        if actual != money(amount):
            result["issues"].append("La deducción no coincide con el cierre (fórmula o ajuste adicional): " + code)
    result["status"] = "incomplete" if result["issues"] else "ready"
    result["employee_applied"] = expected
    doc.monthly_settlement_snapshot = json.dumps(result, default=str, ensure_ascii=False, sort_keys=True)
    ctx["calculation"] = result


def populate_employer(doc):
    ctx = getattr(doc, "_pp_monthly", None)
    if not ctx:
        return False
    doc.set("employer_contributions", [])
    if ctx["close"]:
        for row in ctx["calculation"]["employer"]:
            doc.append("employer_contributions", {
                "contribution_code": row["code"], "contribution_name": row["name"],
                "base_amount": float(row["base_amount"]), "rate": float(row["rate_percent"]),
                "ceiling": float(row["ceiling"]), "amount": float(row["amount"]),
                "expense_account": row["expense_account"], "payable_account": row["payable_account"],
                "rule_effective_from": row["rule_effective_from"],
            })
    return True


def before_submit(doc):
    if not settings_for(doc):
        return
    # Lock acquired at the start of validate; repeat only for direct lifecycle calls.
    lock_employee(doc)
    doc.calculate_net_pay()
    snapshot = json.loads(doc.monthly_settlement_snapshot or "{}")
    if snapshot.get("issues"):
        frappe.throw("No se puede confirmar el acumulado mensual: " + "; ".join(snapshot["issues"]))


def before_cancel(doc):
    # Preserve dependencies even when the feature has subsequently been disabled.
    if not doc.meta.has_field("monthly_settlement_snapshot"):
        return
    lock_employee(doc)
    first, last = month_bounds(doc.end_date)
    rows = frappe.db.sql(
        """select name, monthly_settlement_snapshot from `tabSalary Slip`
           where employee=%s and company=%s and docstatus=1 and name!=%s
           and start_date<=%s and end_date>=%s for update""",
        (doc.employee, doc.company, doc.name, last, first), as_dict=True,
    )
    for row in rows:
        snapshot = json.loads(row.monthly_settlement_snapshot or "{}")
        if snapshot.get("close") and any(s["name"] == doc.name for s in snapshot.get("sources", [])):
            frappe.throw("Resuelva primero el cierre confirmado " + row.name + " que utiliza este recibo.")


def is_close(doc):
    snapshot = json.loads(doc.get("monthly_settlement_snapshot") or "{}")
    if snapshot:
        return bool(snapshot.get("close"))
    return bool(doc.get("mid_month_start") or doc.payroll_frequency == "Monthly")
