"""Read-only calendar comparison. Never called by settlement or scheduler paths."""
import hashlib
import json
from datetime import datetime, time, timedelta

import frappe
from frappe import _
from frappe.utils import flt, get_datetime, getdate

from powerpro.controllers.overtime import (
    _get_checkins, _get_verified_regular_overtime_before, get_schedule_context,
)
from powerpro.payroll_rules.overtime import (
    WorkInterval, build_work_intervals, coerce_time,
    get_regular_35_percent_cap, reconcile_authorized_intervals,
)
from powerpro.payroll_rules.overtime_calendar import (
    HOUR_FIELDS, calendar_dates, reconcile_calendar_intervals,
)
from powerpro.payroll_rules.overtime_cash_settlement import calculate_cash_settlement
from powerpro.controllers.overtime_weekly import get_weekly_evidence

ALLOWED_SOURCES = {"Overtime Authorization", "Retroactive Overtime Adjustment"}
VERSION = "calendar-preview-v3-shift-corrections"


@frappe.whitelist()
def get_work_call_comparison_options(work_call):
    call = frappe.get_doc("Overtime Work Call", work_call)
    call.check_permission("read")
    rows = frappe.get_list("Overtime Authorization", filters={
        "overtime_work_call": call.name, "docstatus": ["<", 2],
    }, fields=["name", "employee_name", "work_date"],
        order_by="work_date asc, employee_name asc", limit_page_length=101)
    return {"rows": rows[:100], "has_more": len(rows) > 100}


@frappe.whitelist()
def get_calendar_comparison(doctype, name):
    if doctype not in ALLOWED_SOURCES:
        frappe.throw(_("Seleccione una autorización o un ajuste retroactivo."))
    doc = frappe.get_doc(doctype, name)
    doc.check_permission("read")
    if doc.docstatus == 2:
        frappe.throw(_("No se comparan documentos cancelados."))
    try:
        return _compare(doc)
    except (ValueError, TypeError, KeyError) as exc:
        frappe.throw(_("No se pudo comparar el calendario: {0}").format(str(exc)))


def _read_rows(value):
    rows = frappe.parse_json(value or "[]")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("La evidencia guardada no contiene una lista de intervalos o marcaciones.")
    return rows


def _evidence(doc):
    source = doc.get("reconciliation_source")
    if source == "Presumed Attendance":
        raise ValueError("La asistencia presumida no es evidencia de trabajo. Requiere revisión de Gestión Humana.")
    if source in {"Manual Verification", "HR Exception"}:
        raw = doc.get("manual_worked_intervals") or doc.get("reconciliation_intervals")
        rows = _read_rows(raw)
        if not rows:
            raise ValueError("Faltan los intervalos de la verificación manual.")
        warnings = [] if doc.get("manual_worked_intervals") else [
            "Los intervalos guardados pueden estar recortados por la conciliación anterior."
        ]
        return ([WorkInterval(get_datetime(row["start"]), get_datetime(row["end"])) for row in rows],
                warnings, "Verificación manual guardada", rows)
    if doc.get("reconciled_on"):
        rows = _read_rows(doc.get("source_checkins"))
        if not rows:
            raise ValueError("La instantánea no contiene marcaciones. No se reemplazará por evidencia actual.")
        label = "Marcaciones de la instantánea guardada"
    else:
        rows = [dict(row) for row in _get_checkins(doc.employee, getdate(doc.work_date))]
        label = "Marcaciones actuales"
    intervals, warnings = build_work_intervals(rows)
    if not rows:
        warnings.append("No hay marcaciones disponibles; el resultado no confirma ausencia ni trabajo realizado.")
    return intervals, warnings, label, rows


def _compare(doc):
    start, end = get_datetime(doc.authorization_start), get_datetime(doc.authorization_end)
    days = list(calendar_dates(start, end))
    if start.date() != getdate(doc.work_date) or end > datetime.combine(start.date(), time.min) + timedelta(days=2):
        raise ValueError("La ventana debe comenzar en la fecha de trabajo y caber en las dos fechas de evidencia.")
    settings = frappe.get_single("DGII Payroll Settings")
    contexts = []
    for day in days:
        context = get_schedule_context(day, doc.shift_type, doc.holiday_list)
        context["date"] = str(day)
        contexts.append(context)
    # Recover the tail of an ordinary night shift when it overlaps the first day.
    previous = get_schedule_context(days[0] - timedelta(days=1), doc.shift_type, doc.holiday_list)
    if previous.get("shift_end") and get_datetime(previous["shift_end"]) > datetime.combine(days[0], time.min):
        if not previous.get("holiday_list_covers_work_date"):
            raise ValueError("El calendario no cubre el turno nocturno del día anterior.")
        contexts.insert(0, {**previous, "date": str(days[0] - timedelta(days=1))})
    initial = next(row for row in contexts if row["date"] == str(days[0]))
    cap = get_regular_35_percent_cap(settings.weekly_expected_hours, settings.max_weekly_extra_hours)
    intervals, warnings, evidence_label, evidence = _evidence(doc)
    weekly_before = {}
    for day in days:
        week = str(day - timedelta(days=day.weekday()))
        if week in weekly_before:
            continue
        reference = frappe._dict(doc.as_dict())
        reference.work_date = day
        reference.authorization_start = max(start, datetime.combine(day, time.min))
        weekly_before[week] = _get_verified_regular_overtime_before(reference)
    night_start = coerce_time(settings.start_night_hours, time(21))
    night_end = coerce_time(settings.end_night_hours, time(7))
    shared = dict(authorization_start=start, authorization_end=end,
                  maximum_hours=doc.maximum_hours, intervals=intervals,
                  regular_35_percent_cap=cap, night_start=night_start, night_end=night_end)
    baseline = reconcile_authorized_intervals(
        **shared, day_classification=initial["classification"],
        shift_start=initial["shift_start"], shift_end=initial["shift_end"],
        approved_regular_overtime_before=weekly_before[str(days[0] - timedelta(days=days[0].weekday()))],
        warnings=warnings,
    )
    proposed = reconcile_calendar_intervals(**shared, contexts=contexts,
                                            regular_hours_before_by_week=weekly_before)
    pricing, pricing_note = _pricing(doc, baseline, proposed, settings)
    weekly_evidence = get_weekly_evidence(doc, weekly_before, settings.max_weekly_extra_hours)
    warnings.extend(warning for context in contexts for warning in context.get("warnings", []))
    result = {
        "doctype": doc.doctype, "name": doc.name, "employee_name": doc.employee_name,
        "read_only": True, "saved_documents": 0, "settlement_enabled": False,
        "calculation_version": VERSION, "evidence_source": evidence_label,
        "baseline": {field: baseline[field] for field in HOUR_FIELDS},
        "proposed": proposed,
        "difference": {field: round(proposed[field] - baseline[field], 4) for field in HOUR_FIELDS},
        "warnings": list(dict.fromkeys(warnings)), "pricing": pricing, "pricing_note": pricing_note,
        "assumptions": [
            "El cálculo vigente se vuelve a calcular con la misma evidencia; no representa necesariamente el importe guardado.",
            "Se conservan las bandas y porcentajes actuales. La jornada nocturna completa, los recargos combinados y el total semanal real siguen pendientes de validación.",
            "Los importes son ilustrativos; esta comparación no verifica asistencia ni permite liquidar.",
        ],
        "contexts": contexts, "weekly_before": weekly_before, "weekly_evidence": weekly_evidence,
    }
    provenance = {"version": VERSION, "source": doc.name, "modified": str(doc.modified),
                  "window": [str(start), str(end), doc.maximum_hours], "evidence": evidence,
                  "contexts": contexts, "weekly_before": weekly_before, "weekly_evidence": weekly_evidence,
                  "rates": [settings.extra_hours_rate, settings.extraordinary_hours_rate,
                            settings.night_hours_rate], "night_window": [str(night_start), str(night_end)],
                  "weekly_cap": cap, "pricing": pricing}
    result["comparison_hash"] = hashlib.sha256(json.dumps(provenance, sort_keys=True, default=str).encode()).hexdigest()
    return result


def _pricing(doc, baseline, proposed, settings):
    # Do not expose a salary assignment merely because a user can read an overtime request.
    rate = flt(doc.get("settlement_hourly_rate"))
    source = "Tarifa guardada en la liquidación"
    if rate <= 0:
        if not frappe.has_permission("Salary Structure Assignment", "read"):
            return None, "Comparación de horas; no hay acceso a la tarifa salarial."
        # Query the effective assignment first, but never expose its values without
        # a document permission check. Do not substitute an older accessible salary.
        assignments = frappe.get_all("Salary Structure Assignment", filters={
            "employee": doc.employee, "company": doc.company, "docstatus": 1,
            "from_date": ["<=", doc.work_date],
        }, fields=["name"], order_by="from_date desc, creation desc", limit=1)
        if not assignments:
            return None, "No hay una tarifa salarial válida para la fecha de trabajo."
        salary_doc = frappe.get_doc("Salary Structure Assignment", assignments[0].name)
        if not frappe.has_permission(salary_doc.doctype, "read", doc=salary_doc):
            return None, "Comparación de horas; no hay acceso a la tarifa salarial."
        rate = flt(salary_doc.get("salary_per_hour"))
        if rate <= 0 and flt(salary_doc.get("base")) > 0:
            rate = round(flt(salary_doc.base) / 23.83 / 8, 2)
        if rate <= 0:
            return None, "No hay una tarifa salarial válida para la fecha de trabajo."
        source = "Tarifa de la asignación salarial para la fecha de trabajo"
    rates = dict(hourly_rate=rate, regular_overtime_percent=settings.extra_hours_rate,
                 extraordinary_overtime_percent=settings.extraordinary_hours_rate,
                 night_hours_percent=settings.night_hours_rate)
    totals = []
    for result in (baseline, proposed):
        if flt(result["weekly_rest_hours"]):
            return None, "Hay horas de descanso semanal: su liquidación permanece pendiente de definición."
        totals.append(calculate_cash_settlement(**rates, **{
            field: result[field] for field in HOUR_FIELDS if field != "verified_hours"
        }))
    currency = frappe.db.get_value("Company", doc.company, "default_currency")
    return {"currency": currency, "hourly_rate": rate, "rate_source": source,
            "baseline": totals[0], "proposed": totals[1],
            "difference": round(totals[1]["total_amount"] - totals[0]["total_amount"], 2)}, None
