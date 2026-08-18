"""Pure calculation rules for IGC employer payroll contributions."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from powerpro.payroll_rules.dominican_republic import get_tss_rule


DEDICATED_MODE = "Dedicated Journal Entries"
LEGACY_MODE = "Salary Component Pairs"

TSS_PAYABLE = "213108 - TESORERIA DE LA SEGURIDAD SOCIAL POR PAGAR - IGC"
INFOTEP_PAYABLE = "213109 - INFOTEP POR PAGAR - IGC"
TSS_EXPENSE = "612101 - TSS PROPORCION EMPLEADOR - IGC"
SRL_EXPENSE = "612201 - APORTE RIESGOS LABORALES (SRL) - IGC"
INFOTEP_EXPENSE = "612401 - INFOTEP - IGC"

AFP_RATE = Decimal("0.0710")
ARS_RATE = Decimal("0.0709")


@dataclass(frozen=True)
class EmployerContribution:
	code: str
	name: str
	base_amount: Decimal
	rate_percent: Decimal
	ceiling: Decimal
	amount: Decimal
	expense_account: str
	payable_account: str
	rule_effective_from: object


def calculate_employer_contributions(
	monthly_salary,
	on_date,
	commissions=0,
	statutory_vacation=0,
	infotep_rate_percent=Decimal("1"),
	srl_rate_percent=Decimal("1.2"),
):
	"""Return the four monthly employer obligations as immutable snapshots."""
	rule = get_tss_rule(on_date)
	salary = max(_decimal(monthly_salary), Decimal("0"))
	commission = max(_decimal(commissions), Decimal("0"))
	vacation = max(_decimal(statutory_vacation), Decimal("0"))
	infotep_rate = _decimal(infotep_rate_percent) / Decimal("100")
	srl_rate = _decimal(srl_rate_percent) / Decimal("100")
	infotep_base = salary + commission
	srl_uncapped_base = salary + commission + vacation
	srl_base = min(srl_uncapped_base, rule.srl_ceiling)

	return (
		_build("AFP", "AFP Empleador", salary, AFP_RATE, 0, TSS_EXPENSE, TSS_PAYABLE, rule.effective_from),
		_build("ARS", "ARS Empleador", salary, ARS_RATE, 0, TSS_EXPENSE, TSS_PAYABLE, rule.effective_from),
		_build(
			"INFOTEP",
			"INFOTEP Empleador",
			infotep_base,
			infotep_rate,
			0,
			INFOTEP_EXPENSE,
			INFOTEP_PAYABLE,
			rule.effective_from,
		),
		_build(
			"SRL",
			"SRL Empleador",
			srl_base,
			srl_rate,
			rule.srl_ceiling,
			SRL_EXPENSE,
			TSS_PAYABLE,
			rule.effective_from,
		),
	)


def _build(code, name, base, rate, ceiling, expense_account, payable_account, effective_from):
	return EmployerContribution(
		code=code,
		name=name,
		base_amount=_money(base),
		rate_percent=rate * Decimal("100"),
		ceiling=_money(ceiling),
		amount=_money(base * rate),
		expense_account=expense_account,
		payable_account=payable_account,
		rule_effective_from=effective_from,
	)


def _money(value):
	return _decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _decimal(value):
	return value if isinstance(value, Decimal) else Decimal(str(value or 0))
