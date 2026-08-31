# Copyright (c) 2026, PowerPro contributors
# For license information, please see license.txt

"""Payroll-safe overtime summary built from approved settlement snapshots."""

from collections import defaultdict
from datetime import date, datetime
import json

import frappe
from frappe import _
from frappe.utils import flt, getdate


DAILY_DIVISOR = 23.83
HOURS_PER_DAY = 8
LINE_COMPONENTS = {
    "Horas Extras 35%": "amount_35",
    "Horas Extras 100%": "amount_100",
    "Horas Nocturnas": "amount_night",
}


def execute(filters=None):
    filters = frappe._dict(filters or {})
    _validate_filters(filters)

    adjustments = _get_adjustments(filters)
    assignments = _get_assignments(adjustments)
    data = summarize_adjustments(adjustments, assignments)
    return get_columns(), data, None, None, get_report_summary(data)


def get_columns():
    currency_options = "currency"
    return [
        {
            "fieldname": "employee_name",
            "label": _("Nombre completo"),
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "fieldname": "salary",
            "label": _("Salario"),
            "fieldtype": "Currency",
            "options": currency_options,
            "width": 115,
        },
        {
            "fieldname": "half_month_salary",
            "label": _("Quincena"),
            "fieldtype": "Currency",
            "options": currency_options,
            "width": 115,
        },
        {
            "fieldname": "daily_salary",
            "label": _("Salario diario"),
            "fieldtype": "Currency",
            "options": currency_options,
            "width": 115,
        },
        {
            "fieldname": "hourly_rate",
            "label": _("Valor hora"),
            "fieldtype": "Currency",
            "options": currency_options,
            "width": 105,
        },
        {
            "fieldname": "dates",
            "label": _("Fecha"),
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "fieldname": "hours_35",
            "label": _("35%"),
            "fieldtype": "Float",
            "precision": 2,
            "width": 90,
        },
        {
            "fieldname": "hours_100",
            "label": _("100%"),
            "fieldtype": "Float",
            "precision": 2,
            "width": 95,
        },
        {
            "fieldname": "night_hours",
            "label": _("Noct."),
            "fieldtype": "Float",
            "precision": 2,
            "width": 95,
        },
        {
            "fieldname": "total_hours",
            "label": _("Total horas"),
            "fieldtype": "Float",
            "precision": 2,
            "width": 100,
        },
        {
            "fieldname": "amount_35",
            "label": _("Extras 35%"),
            "fieldtype": "Currency",
            "options": currency_options,
            "width": 120,
        },
        {
            "fieldname": "amount_100",
            "label": _("Extras 100%"),
            "fieldtype": "Currency",
            "options": currency_options,
            "width": 125,
        },
        {
            "fieldname": "amount_night",
            "label": _("Noct. 15%"),
            "fieldtype": "Currency",
            "options": currency_options,
            "width": 110,
        },
        {
            "fieldname": "total_amount",
            "label": _("Monto total a pagar"),
            "fieldtype": "Currency",
            "options": currency_options,
            "width": 145,
        },
        {
            "fieldname": "currency",
            "label": _("Moneda"),
            "fieldtype": "Link",
            "options": "Currency",
            "hidden": 1,
        },
    ]


def _validate_filters(filters):
    missing = [field for field in ("company", "from_date", "to_date") if not filters.get(field)]
    if missing:
        frappe.throw(_("Company, From Date, and To Date are required."))
    if getdate(filters.from_date) > getdate(filters.to_date):
        frappe.throw(_("From Date cannot be after To Date."))


def _get_adjustments(filters):
    conditions = {
        "company": filters.company,
        "work_date": ["between", [filters.from_date, filters.to_date]],
        "docstatus": 1,
        "status": "Approved",
        "planned_settlement": "Cash",
        "settlement_status": ["in", ["Created", "Paid"]],
    }
    for fieldname in ("employee", "department", "settlement_status"):
        if filters.get(fieldname):
            conditions[fieldname] = filters[fieldname]

    fields = [
            "name",
            "employee",
            "employee_name",
            "company",
            "department",
            "work_date",
            "regular_35_hours",
            "regular_100_hours",
            "holiday_100_hours",
            "night_hours",
            "weekly_rest_hours",
            "settlement_hourly_rate",
            "settlement_amount",
            "settlement_currency",
            "settlement_status",
            "settlement_breakdown",
        ]
    rows = []
    for doctype in ("Retroactive Overtime Adjustment", "Overtime Authorization"):
        if not frappe.db.exists("DocType", doctype):
            continue
        rows.extend(
            frappe.get_list(
                doctype,
                filters=conditions,
                fields=fields,
                order_by="employee_name asc, work_date asc, name asc",
                limit_page_length=0,
            )
        )
    return sorted(
        rows,
        key=lambda row: (
            (row.get("employee_name") or "").casefold(),
            getdate(row.get("work_date")),
            row.get("name") or "",
        ),
    )


def _get_assignments(adjustments):
    names = {
        parsed.get("salary_structure_assignment")
        for parsed in (_parse_breakdown(row.get("settlement_breakdown")) for row in adjustments)
        if parsed.get("salary_structure_assignment")
    }
    if not names:
        return {}

    rows = frappe.get_list(
        "Salary Structure Assignment",
        filters={"name": ["in", sorted(names)], "docstatus": 1},
        fields=["name", "base"],
        limit_page_length=0,
    )
    return {row.name: flt(row.base) for row in rows}


def summarize_adjustments(adjustments, assignments=None):
    """Aggregate immutable submitted rows; night hours remain a non-additive overlay."""
    assignments = assignments or {}
    grouped = defaultdict(_empty_summary)

    for row in adjustments:
        row = dict(row)
        breakdown = _parse_breakdown(row.get("settlement_breakdown"))
        hourly_rate = flt(row.get("settlement_hourly_rate") or breakdown.get("hourly_rate"))
        assignment_name = breakdown.get("salary_structure_assignment")
        salary = flt(assignments.get(assignment_name))
        if not salary and hourly_rate:
            salary = round(hourly_rate * DAILY_DIVISOR * HOURS_PER_DAY, 2)

        currency = row.get("settlement_currency") or breakdown.get("currency")
        key = (row.get("employee"), currency, round(salary, 2), round(hourly_rate, 2))
        summary = grouped[key]
        summary.update({
            "employee": row.get("employee"),
            "employee_name": row.get("employee_name"),
            "currency": currency,
            "salary": round(salary, 2),
            "half_month_salary": round(salary / 2, 2),
            "daily_salary": round(salary / DAILY_DIVISOR, 2),
            "hourly_rate": round(hourly_rate, 2),
        })

        summary["_dates"].add(_as_date(row.get("work_date")))
        summary["hours_35"] += flt(row.get("regular_35_hours"))
        summary["hours_100"] += flt(row.get("regular_100_hours")) + flt(row.get("holiday_100_hours"))
        summary["night_hours"] += flt(row.get("night_hours"))

        amounts = _line_amounts(breakdown)
        summary["amount_35"] += amounts["amount_35"]
        summary["amount_100"] += amounts["amount_100"]
        summary["amount_night"] += amounts["amount_night"]
        summary["total_amount"] += flt(
            row.get("settlement_amount") or breakdown.get("total_amount")
        )

    result = []
    for summary in grouped.values():
        summary["total_hours"] = summary["hours_35"] + summary["hours_100"]
        summary["dates"] = ", ".join(_format_date(value) for value in sorted(summary.pop("_dates")))
        for fieldname in (
            "hours_35",
            "hours_100",
            "night_hours",
            "total_hours",
            "amount_35",
            "amount_100",
            "amount_night",
            "total_amount",
        ):
            summary[fieldname] = round(summary[fieldname], 2)
        result.append(summary)

    return sorted(result, key=lambda row: ((row.get("employee_name") or "").casefold(), row["hourly_rate"]))


def get_report_summary(data):
    currencies = {row.get("currency") for row in data if row.get("currency")}
    currency = next(iter(currencies)) if len(currencies) == 1 else None
    return [
        {
            "value": len({row.get("employee") for row in data if row.get("employee")}),
            "indicator": "Blue",
            "label": _("Empleados"),
            "datatype": "Int",
        },
        {
            "value": round(sum(flt(row.get("total_hours")) for row in data), 2),
            "indicator": "Blue",
            "label": _("Total horas"),
            "datatype": "Float",
        },
        {
            "value": round(sum(flt(row.get("total_amount")) for row in data), 2),
            "indicator": "Green",
            "label": _("Monto total a pagar"),
            "datatype": "Currency",
            "currency": currency,
        },
    ]


def _empty_summary():
    return {
        "employee": None,
        "employee_name": None,
        "currency": None,
        "salary": 0.0,
        "half_month_salary": 0.0,
        "daily_salary": 0.0,
        "hourly_rate": 0.0,
        "dates": "",
        "hours_35": 0.0,
        "hours_100": 0.0,
        "night_hours": 0.0,
        "total_hours": 0.0,
        "amount_35": 0.0,
        "amount_100": 0.0,
        "amount_night": 0.0,
        "total_amount": 0.0,
        "_dates": set(),
    }


def _parse_breakdown(value):
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(value or "{}")
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _line_amounts(breakdown):
    amounts = {fieldname: 0.0 for fieldname in LINE_COMPONENTS.values()}
    for line in breakdown.get("lines") or []:
        fieldname = LINE_COMPONENTS.get(line.get("component"))
        if fieldname:
            amounts[fieldname] += flt(line.get("amount"))
    return amounts


def _as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _format_date(value):
    return value.strftime("%d/%m")
