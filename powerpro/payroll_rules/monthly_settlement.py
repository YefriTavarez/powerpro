"""Pure month-end payroll arithmetic. No Frappe imports or database writes."""

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from .dominican_republic import calculate_monthly_isr, get_isr_scale, get_tss_rule
from .employer_contributions import calculate_employer_contributions

VERSION = 2
# Preserve the existing classification of historical rows, which may lack tax flags.
TAXABLE = frozenset(("B", "COM", "VAC", "BVA", "INC", "BNF", "HRE", "HN", "HE"))
MANAGED = frozenset(("BAM", "AFP", "ARS", "MIMP", "BIMP", "ABIMP", "ISRM"))


def money(value=0):
    return Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def taxable_amounts(rows):
    """Use each effective earning row's tax flag, retaining legacy classifications.

    Read the flag stored on the slip, not today's component master. Multiple
    payments of one component are accumulated once, including mixed tax flags.
    Callers supply only earning rows; statistical rows never represent paid income.
    """
    amounts = {}
    for row in rows:
        abbr = row.get("abbr")
        if row.get("do_not_include_in_total"):
            continue
        if abbr in TAXABLE or row.get("is_tax_applicable"):
            amounts[abbr] = amounts.get(abbr, money()) + money(row.get("amount"))
    return amounts


def as_date(value):
    return value if isinstance(value, date) else date.fromisoformat(str(value))


def month_bounds(value):
    value = as_date(value)
    return value.replace(day=1), value.replace(day=monthrange(value.year, value.month)[1])


def period_issues(current, history, joining_date=None, relieving_date=None):
    """Validate an ordinary monthly/bimonthly settlement, using submitted coverage."""
    start, end = as_date(current["start_date"]), as_date(current["end_date"])
    first, last = month_bounds(end)
    issues = []
    if start < first or start > end:
        issues.append("El período cruza de mes o tiene fechas inválidas.")
    if current.get("payroll_frequency") not in ("Monthly", "Bimonthly"):
        issues.append("El acumulado admite únicamente nómina mensual o quincenal.")
    if relieving_date and first <= as_date(relieving_date) < last:
        issues.append("La salida antes del cierre requiere liquidación específica.")
    submitted = [s for s in history if s["docstatus"] == 1]
    for slip in submitted:
        a, b = as_date(slip["start_date"]), as_date(slip["end_date"])
        if a < first or b > last:
            issues.append("Existe un recibo confirmado que cruza el mes: " + slip["name"])
        if a <= end and b >= start:
            issues.append("Existe un recibo confirmado solapado: " + slip["name"])
        elif b >= end:
            issues.append("Existe un recibo posterior o un cierre confirmado: " + slip["name"])
    if end == last:
        covered = set()
        for slip in submitted:
            a, b = as_date(slip["start_date"]), as_date(slip["end_date"])
            if b >= start:
                continue
            for offset in range((b - a).days + 1):
                day = a + timedelta(days=offset)
                if day in covered:
                    issues.append("Hay períodos anteriores confirmados solapados.")
                    break
                covered.add(day)
        day = max(first, as_date(joining_date)) if joining_date else first
        missing = []
        while day < start:
            if day not in covered:
                missing.append(day.isoformat())
            day += timedelta(days=1)
        if missing:
            issues.append("Falta confirmar el período previo: " + missing[0] + " a " + missing[-1])
    return list(dict.fromkeys(issues))


def calculate(current, previous, previous_deductions, previous_employer, on_date,
              dependents=0, employee_afp_rate=2.87, employee_ars_rate=3.04,
              infotep_rate=1, srl_rate=1.2, *, current_taxable=None, previous_taxable=None,
              employer_excluded=False):
    """Amounts are already prorated. Returns monthly obligations and remaining balances."""
    totals = {key: money(current.get(key)) + money(previous.get(key)) for key in current.keys() | previous.keys()}
    salary, commission, vacation = (totals.get(key, money()) for key in ("B", "COM", "VAC"))
    tss = get_tss_rule(on_date)
    scale = get_isr_scale(on_date)
    if scale.effective_from.year != as_date(on_date).year:
        raise ValueError("No hay escala ISR verificada para el año del cierre.")
    cotizable = max(salary + commission + vacation, money())
    afp_base, ars_base = min(cotizable, tss.pension_ceiling), min(cotizable, tss.sfs_ceiling)
    afp = money(afp_base * Decimal(str(employee_afp_rate)) / 100)
    ars = money(ars_base * Decimal(str(employee_ars_rate)) / 100)
    # Optional row-derived inputs let new taxable components participate without
    # changing contribution bases or the legacy pure-calculator calling contract.
    current_taxable = {key: money(value) for key, value in
                       (current_taxable if current_taxable is not None else
                        {k: v for k, v in current.items() if k in TAXABLE}).items()}
    previous_taxable = {key: money(value) for key, value in
                        (previous_taxable if previous_taxable is not None else
                         {k: v for k, v in previous.items() if k in TAXABLE}).items()}
    taxable = sum(current_taxable.values(), money()) + sum(previous_taxable.values(), money())
    dp = money(dependents) + money(previous_deductions.get("DP"))
    income_base = max(taxable - afp - ars - dp, money())
    obligations = {"AFP": afp, "ARS": ars, "ISRM": calculate_monthly_isr(income_base, on_date)}
    employer = [] if employer_excluded else calculate_employer_contributions(
        salary, on_date, commission, vacation, infotep_rate, srl_rate,
        actual_monthly_base=True,
    )
    issues = []
    employee = {}
    for code, total in obligations.items():
        prior = money(previous_deductions.get(code))
        balance = money(total - prior)
        if balance < 0:
            issues.append("Retención previa mayor que obligación mensual: " + code)
        employee[code] = {"total": total, "previous": prior, "balance": balance, "amount": max(balance, money())}
    employer_rows = []
    for row in employer:
        prior = money(previous_employer.get(row.code))
        balance = money(row.amount - prior)
        if balance < 0:
            issues.append("Aporte previo mayor que obligación mensual: " + row.code)
        employer_rows.append({**vars(row), "total": row.amount, "previous": prior,
                              "balance": balance, "amount": max(balance, money())})
    return {
        "version": VERSION, "on_date": str(on_date), "current": current, "previous": previous,
        "current_taxable": current_taxable, "previous_taxable": previous_taxable,
        "totals": totals, "salary": salary, "taxable_earnings": taxable,
        "cotizable": cotizable, "afp_base": afp_base, "ars_base": ars_base,
        "dependents": dp, "income_tax_base": income_base,
        "employee": employee, "employer": employer_rows, "issues": issues,
        "employer_excluded": bool(employer_excluded),
        "rules": {"tss_effective_from": str(tss.effective_from),
                  "isr_effective_from": str(scale.effective_from),
                  "pension_ceiling": tss.pension_ceiling, "sfs_ceiling": tss.sfs_ceiling,
                  "srl_ceiling": tss.srl_ceiling, "employee_afp_rate": employee_afp_rate,
                  "employee_ars_rate": employee_ars_rate},
    }
