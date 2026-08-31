"""Pure conversion rules for the overtime compensatory-hours bank."""

from __future__ import annotations

import math


def calculate_compensatory_credit(
	*,
	active_hours_before,
	current_hours,
	effective_days_before,
	hours_per_day,
	leave_increment,
):
	active_hours_before = max(float(active_hours_before or 0), 0)
	current_hours = max(float(current_hours or 0), 0)
	effective_days_before = max(float(effective_days_before or 0), 0)
	hours_per_day = float(hours_per_day or 0)
	leave_increment = float(leave_increment or 0)
	if current_hours <= 0:
		raise ValueError("Current overtime hours must be greater than zero")
	if hours_per_day <= 0:
		raise ValueError("Hours per leave day must be greater than zero")
	if leave_increment <= 0 or leave_increment > 1:
		raise ValueError("Leave increment must be greater than zero and at most one day")

	total_hours = active_hours_before + current_hours
	target_days = _floor_to_increment(
		total_hours / hours_per_day,
		leave_increment,
	)
	days_to_credit = max(target_days - effective_days_before, 0)
	residual_hours = max(total_hours - target_days * hours_per_day, 0)
	prior_residual_hours = max(
		active_hours_before - effective_days_before * hours_per_day,
		0,
	)
	return {
		"active_hours_before": round(active_hours_before, 4),
		"current_hours": round(current_hours, 4),
		"total_active_hours": round(total_hours, 4),
		"effective_days_before": round(effective_days_before, 4),
		"target_days": round(target_days, 4),
		"days_to_credit": round(days_to_credit, 4),
		"prior_residual_hours": round(prior_residual_hours, 4),
		"residual_hours": round(residual_hours, 4),
		"hours_per_day": round(hours_per_day, 4),
		"leave_increment": round(leave_increment, 4),
	}


def calculate_compensatory_reversal(
	*,
	active_hours_before,
	hours_to_reverse,
	effective_days_before,
	hours_per_day,
	leave_increment,
):
	active_hours_before = max(float(active_hours_before or 0), 0)
	hours_to_reverse = max(float(hours_to_reverse or 0), 0)
	effective_days_before = max(float(effective_days_before or 0), 0)
	hours_per_day = float(hours_per_day or 0)
	leave_increment = float(leave_increment or 0)
	if hours_to_reverse <= 0 or hours_to_reverse > active_hours_before + 1e-7:
		raise ValueError("Reversal hours must belong to the active overtime bank")
	if hours_per_day <= 0:
		raise ValueError("Hours per leave day must be greater than zero")
	if leave_increment <= 0 or leave_increment > 1:
		raise ValueError("Leave increment must be greater than zero and at most one day")

	active_hours_after = max(active_hours_before - hours_to_reverse, 0)
	target_days_after = _floor_to_increment(
		active_hours_after / hours_per_day,
		leave_increment,
	)
	days_to_reverse = max(effective_days_before - target_days_after, 0)
	residual_hours_after = max(
		active_hours_after - target_days_after * hours_per_day,
		0,
	)
	return {
		"active_hours_before": round(active_hours_before, 4),
		"hours_to_reverse": round(hours_to_reverse, 4),
		"active_hours_after": round(active_hours_after, 4),
		"effective_days_before": round(effective_days_before, 4),
		"target_days_after": round(target_days_after, 4),
		"days_to_reverse": round(days_to_reverse, 4),
		"residual_hours_after": round(residual_hours_after, 4),
	}


def _floor_to_increment(value, increment):
	return math.floor((float(value) + 1e-9) / increment) * increment

