"""Date-effective Dominican payroll references.

Sources:
- TSS Resolution 01-2024 and TSS notice dated 2024-02-08.
- TSS Resolution 01-2025 dated 2025-03-11.
- TSS User Guide 2024, employer contribution rates and cotizable bases.
- INFOTEP Law 116-80, Article 24.
- DGII Contributor Guide 11, Retenciones del ISR, July 2025.
- DGII official help CA4598, confirming the 2026 scale remains in effect
  until the new statutory brackets begin in fiscal year 2027.

This module performs no database access and does not alter Salary Slips.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP


TSS_RESOLUTION_2024_URL = "https://www.tss.gob.do/assets/reso01-2024.pdf"
TSS_RESOLUTION_2025_URL = "https://www.tss.gob.do/assets/reso01-2025.pdf"
DGII_ISR_GUIDE_URL = (
    "https://dgii.gov.do/publicacionesOficiales/bibliotecaVirtual/contribuyentes/"
    "retencionesRetribucionesComplementarias/Documents/2-Guia-11-Retenciones%20del%20Impuesto%20Sobre%20la%20Renta.pdf"
)
TSS_USER_GUIDE_URL = "https://www.tss.gob.do/assets/guiausuario24b.pdf"
INFOTEP_LAW_116_80_URL = (
    "https://www.infotep.gob.do/index.php/marco-legal/category/14-leyes"
    "?download=19%3Aley116"
)

INFOTEP_EMPLOYER_RATE = Decimal("0.01")
DEFAULT_IGC_SRL_RATE = Decimal("0.012")


@dataclass(frozen=True)
class TSSRule:
    effective_from: date
    national_minimum_salary: Decimal
    srl_ceiling: Decimal
    sfs_ceiling: Decimal
    pension_ceiling: Decimal
    source_url: str


TSS_RULES = (
    TSSRule(
        effective_from=date(2024, 2, 1),
        national_minimum_salary=Decimal("19352.50"),
        srl_ceiling=Decimal("77410.00"),
        sfs_ceiling=Decimal("193525.00"),
        pension_ceiling=Decimal("387050.00"),
        source_url=TSS_RESOLUTION_2024_URL,
    ),
    TSSRule(
        effective_from=date(2025, 4, 1),
        national_minimum_salary=Decimal("21674.80"),
        srl_ceiling=Decimal("86699.20"),
        sfs_ceiling=Decimal("216748.00"),
        pension_ceiling=Decimal("433496.00"),
        source_url=TSS_RESOLUTION_2025_URL,
    ),
    TSSRule(
        effective_from=date(2026, 2, 1),
        national_minimum_salary=Decimal("23223.00"),
        srl_ceiling=Decimal("92892.00"),
        sfs_ceiling=Decimal("232230.00"),
        pension_ceiling=Decimal("464460.00"),
        source_url=TSS_RESOLUTION_2025_URL,
    ),
)


@dataclass(frozen=True)
class ISRScale:
    effective_from: date
    exempt_through: Decimal
    second_through: Decimal
    third_through: Decimal
    second_rate: Decimal
    third_fixed: Decimal
    third_rate: Decimal
    fourth_fixed: Decimal
    fourth_rate: Decimal
    source_url: str


ISR_SCALES = (
    ISRScale(
        effective_from=date(2025, 1, 1),
        exempt_through=Decimal("416220.00"),
        second_through=Decimal("624329.00"),
        third_through=Decimal("867123.00"),
        second_rate=Decimal("0.15"),
        third_fixed=Decimal("31216.00"),
        third_rate=Decimal("0.20"),
        fourth_fixed=Decimal("79776.00"),
        fourth_rate=Decimal("0.25"),
        source_url=DGII_ISR_GUIDE_URL,
    ),
    ISRScale(
        effective_from=date(2026, 1, 1),
        exempt_through=Decimal("416220.00"),
        second_through=Decimal("624329.00"),
        third_through=Decimal("867123.00"),
        second_rate=Decimal("0.15"),
        third_fixed=Decimal("31216.00"),
        third_rate=Decimal("0.20"),
        fourth_fixed=Decimal("79776.00"),
        fourth_rate=Decimal("0.25"),
        source_url=DGII_ISR_GUIDE_URL,
    ),
)


def get_tss_rule(on_date):
    return _latest_rule(TSS_RULES, _as_date(on_date))


def get_isr_scale(on_date):
    return _latest_rule(ISR_SCALES, _as_date(on_date))


def calculate_monthly_isr(monthly_taxable_income, on_date):
    """Calculate monthly ISR from an already-derived monthly taxable base."""
    scale = get_isr_scale(on_date)
    annual = _decimal(monthly_taxable_income) * Decimal("12")

    if annual <= scale.exempt_through:
        annual_tax = Decimal("0")
    elif annual <= scale.second_through:
        annual_tax = (annual - Decimal("416220.01")) * scale.second_rate
    elif annual <= scale.third_through:
        annual_tax = scale.third_fixed + (annual - Decimal("624329.01")) * scale.third_rate
    else:
        annual_tax = scale.fourth_fixed + (annual - Decimal("867123.01")) * scale.fourth_rate

    return (annual_tax / Decimal("12")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_infotep_employer(monthly_salary, commissions=0, rate=INFOTEP_EMPLOYER_RATE):
    """Calculate the monthly employer INFOTEP contribution.

    The normal employer contribution is 1% of salary plus commissions. The
    separate employee withholding on annual profit sharing is intentionally
    outside this payroll component.
    """
    cotizable = max(_decimal(monthly_salary) + _decimal(commissions), Decimal("0"))
    return (cotizable * _decimal(rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_srl_employer(
    monthly_salary,
    on_date,
    commissions=0,
    statutory_vacation=0,
    rate=DEFAULT_IGC_SRL_RATE,
):
    """Calculate monthly employer SRL subject to the date-effective ceiling."""
    cotizable = max(
        _decimal(monthly_salary) + _decimal(commissions) + _decimal(statutory_vacation),
        Decimal("0"),
    )
    capped = min(cotizable, get_tss_rule(on_date).srl_ceiling)
    return (capped * _decimal(rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _latest_rule(rules, on_date):
    applicable = [rule for rule in rules if rule.effective_from <= on_date]
    if not applicable:
        raise ValueError(f"No payroll rule configured for {on_date.isoformat()}")
    return applicable[-1]


def _as_date(value):
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _decimal(value):
    return value if isinstance(value, Decimal) else Decimal(str(value or 0))
