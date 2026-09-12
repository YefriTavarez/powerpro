"""Pure cash-settlement calculations for approved overtime snapshots."""

from decimal import Decimal, ROUND_HALF_UP


REGULAR_35_COMPONENT = "Horas Extras 35%"
EXTRAORDINARY_100_COMPONENT = "Horas Extras 100%"
NIGHT_COMPONENT = "Horas Nocturnas"


def calculate_cash_settlement(
	*,
	hourly_rate,
	regular_35_hours=0,
	regular_100_hours=0,
	holiday_100_hours=0,
	holiday_base_covered_hours=0,
	weekly_rest_hours=0,
	night_hours=0,
	regular_overtime_percent=35,
	extraordinary_overtime_percent=100,
	night_hours_percent=15,
	weekly_rest_overtime_percent=None,
):
	"""Return auditable Additional Salary lines for an approved snapshot.

	Ordinary weekly-rest hours intentionally remain a separate settlement
	category. A legal holiday on weekly rest is already represented once in
	``holiday_100_hours`` by the reconciliation engine.
	"""
	rate = _decimal(hourly_rate)
	if not rate.is_finite() or rate <= 0:
		raise ValueError("Hourly rate must be greater than zero.")

	regular_35 = _non_negative(regular_35_hours, "Regular +35% hours")
	regular_100 = _non_negative(regular_100_hours, "Regular +100% hours")
	holiday_100 = _non_negative(holiday_100_hours, "Legal holiday +100% hours")
	covered = _non_negative(holiday_base_covered_hours, "Holiday base already covered hours")
	if covered > holiday_100:
		raise ValueError("Covered holiday base hours cannot exceed verified holiday hours.")
	weekly_rest = _non_negative(weekly_rest_hours, "Weekly-rest hours")
	night = _non_negative(night_hours, "Night hours")
	regular_percent = _non_negative(
		regular_overtime_percent, "Regular overtime percentage"
	)
	extraordinary_percent = _non_negative(
		extraordinary_overtime_percent, "Extraordinary overtime percentage"
	)
	night_percent = _non_negative(night_hours_percent, "Night-hours percentage")

	lines = []
	_append_line(
		lines,
		component=REGULAR_35_COMPONENT,
		hours=regular_35,
		hourly_rate=rate,
		premium_percent=regular_percent,
		include_base_hour=True,
	)
	_append_line(
		lines,
		component=EXTRAORDINARY_100_COMPONENT,
		hours=regular_100 + holiday_100 - covered,
		hourly_rate=rate,
		premium_percent=extraordinary_percent,
		include_base_hour=True,
	)
	_append_line(
		lines, component=EXTRAORDINARY_100_COMPONENT, hours=covered,
		hourly_rate=rate, premium_percent=extraordinary_percent, include_base_hour=False,
	)
	_append_line(
		lines,
		component=NIGHT_COMPONENT,
		hours=night,
		hourly_rate=rate,
		premium_percent=night_percent,
		include_base_hour=False,
	)
	if weekly_rest_overtime_percent is not None:
		_append_line(lines,component=EXTRAORDINARY_100_COMPONENT,hours=weekly_rest,hourly_rate=rate,
			premium_percent=_non_negative(weekly_rest_overtime_percent,"Weekly rest percentage"),include_base_hour=True)

	return {
		"hourly_rate": float(_money(rate)),
		"holiday_base_covered_hours": float(covered),
		"holiday_base_already_in_salary": float(_money(covered * rate)),
		"lines": lines,
		"total_amount": float(
			_money(sum((_decimal(line["amount"]) for line in lines), Decimal("0")))
		),
		"unsettled_weekly_rest_hours": float(weekly_rest) if weekly_rest_overtime_percent is None else 0,
	}


def _append_line(
	lines,
	*,
	component,
	hours,
	hourly_rate,
	premium_percent,
	include_base_hour,
):
	if hours <= 0:
		return
	multiplier = premium_percent / Decimal("100")
	if include_base_hour:
		multiplier += Decimal("1")
	amount = _money(hours * hourly_rate * multiplier)
	if amount <= 0:
		return
	lines.append({
		"component": component,
		"hours": float(hours),
		"hourly_rate": float(_money(hourly_rate)),
		"premium_percent": float(premium_percent),
		"multiplier": float(multiplier),
		"amount": float(amount),
	})


def _non_negative(value, label):
	value = _decimal(value)
	if not value.is_finite() or value < 0:
		raise ValueError(f"{label} cannot be negative.")
	return value


def _decimal(value):
	return Decimal(str(value or 0))


def _money(value):
	return _decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
