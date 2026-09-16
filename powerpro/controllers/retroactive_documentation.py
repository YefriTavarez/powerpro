"""Documentary closure of historical work; never an entitlement or payroll input."""
import hashlib
import json

import frappe
from frappe import _
from frappe.utils import cint, flt, get_datetime, now_datetime

DT = "Retroactive Overtime Adjustment"
KINDS = {"Already Paid", "Ordinary Work"}
NOTICE = "Registro documental: no verifica ponches ni genera un nuevo pago o descanso."


def enabled(doc):
    return getattr(doc, "doctype", None) == DT and bool(cint(getattr(doc, "historical_documentation", 0)))


def reject_settlement(doc):
    if enabled(doc):
        frappe.throw(_("Un registro histórico documental no puede generar otra liquidación."))


def recorded_intervals(doc):
    """Validate the declared window and optional break without inferring attendance."""
    start, end = get_datetime(doc.authorization_start), get_datetime(doc.authorization_end)
    if end <= start or end > now_datetime():
        frappe.throw(_("La jornada documental debe ser positiva y haber terminado."))
    a, b = doc.get("historical_break_start"), doc.get("historical_break_end")
    if bool(a) != bool(b):
        frappe.throw(_("Indique inicio y fin de la pausa, o deje ambos vacíos."))
    intervals = [(start, end)]
    if a and b:
        a, b = get_datetime(a), get_datetime(b)
        if not start <= a < b <= end:
            frappe.throw(_("La pausa debe ser positiva y estar dentro de la jornada documental."))
        intervals = [(x, y) for x, y in [(start, a), (b, end)] if y > x]
    hours = sum((y - x).total_seconds() / 3600 for x, y in intervals)
    if hours <= 0 or hours > flt(doc.maximum_hours) + .00005:
        frappe.throw(_("Las horas documentadas deben ser positivas y no superar el máximo del ajuste."))
    return [{"start": x.isoformat(), "end": y.isoformat()} for x, y in intervals], hours


def protect_closed(doc):
    before = doc.get_doc_before_save()
    if before and before.docstatus == 1 and (enabled(before) or enabled(doc)):
        frappe.throw(_("El cierre documental es inmutable; cancele y enmiende para corregirlo."))


def ensure_unlinked(doc):
    # Share the employee mutex with payroll/election creation before converting
    # even a draft. Never erase a source's financial summary while links survive.
    frappe.db.get_value("Employee", doc.employee, "name", for_update=True)
    for target, filters in [
        ("Additional Salary", {"ref_doctype": DT, "ref_docname": doc.name, "docstatus": ["<", 2]}),
        ("Overtime Settlement Election", {"retroactive_adjustment": doc.name, "docstatus": ["<", 2]}),
        ("Overtime Compensatory Credit", {"retroactive_adjustment": doc.name, "docstatus": ["<", 2]}),
    ]:
        if frappe.db.exists(target, filters):
            frappe.throw(_("El ajuste tiene {0} vigente; revise ese vínculo antes del cierre documental.").format(target))


def validate(doc):
    protect_closed(doc)
    if not enabled(doc):
        if doc.get("reconciliation_engine") == "Documentary":
            frappe.throw(_("Seleccione registro histórico documental para usar ese modo."))
        return
    if doc.get("historical_disposition") not in KINDS:
        frappe.throw(_("Indique si el registro corresponde a trabajo ya pagado o jornada ordinaria."))
    if not (doc.get("historical_reference") or "").strip():
        frappe.throw(_("Explique el respaldo del registro histórico y cualquier horario estimado."))
    ensure_unlinked(doc)
    _intervals, doc.historical_hours = recorded_intervals(doc)
    doc.reconciliation_engine = "Documentary"
    # Clients cannot present declared hours as verified attendance or payable earnings.
    for field in ("verified_hours", "regular_35_hours", "regular_100_hours", "holiday_100_hours",
                  "weekly_rest_hours", "night_hours", "evidence_settlement_ready", "settlement_amount",
                  "settlement_hourly_rate", "compensatory_hours", "compensatory_days", "compensatory_residual_hours"):
        doc.set(field, 0)
    for field in ("actual_start", "actual_end", "reconciliation_source", "evidence_status",
                  "evidence_snapshot", "reconciliation_intervals", "source_checkins", "reconciled_by",
                  "reconciled_on", "settlement_references", "settlement_breakdown", "settlement_salary_slip",
                  "settlement_created_by", "settlement_created_on", "holiday_cash_status",
                  "settlement_method", "compensatory_credit", "leave_allocation", "approved_by", "approved_on",
                  "historical_snapshot"):
        doc.set(field, None)
    doc.reconciliation_warnings = _(NOTICE)
    doc.settlement_status = "Not Applicable"
    doc.status = "Draft"


def submit(doc):
    """Called only by native submission after its assigned-approver check."""
    doc.check_permission("submit")
    if not doc.approver or doc.approver != frappe.session.user:
        frappe.throw(_("Solo el aprobador asignado puede cerrar el registro histórico."), frappe.PermissionError)
    if not doc.get("historical_acknowledged"):
        frappe.throw(_("Confirme que este cierre solo documenta historia y no solicita otro pago."))
    ensure_unlinked(doc)
    files = frappe.get_all("File", filters={"file_url": doc.get("historical_source_file"),
        "attached_to_doctype": DT, "attached_to_name": doc.name}, pluck="name", limit=1)
    if not doc.get("historical_source_file") or not files:
        frappe.throw(_("Adjunte el documento de respaldo a este ajuste y selecciónelo como fuente histórica."))
    source = frappe.get_doc("File", files[0])
    source.check_permission("read")
    if not source.file_url.startswith(("/private/files/", "/files/")):
        frappe.throw(_("Seleccione un archivo adjunto almacenado en este sitio como respaldo."))
    content = source.get_content()
    if isinstance(content, str):
        content = content.encode()
    intervals, hours = recorded_intervals(doc)
    doc.historical_hours = hours
    doc.historical_snapshot = json.dumps({
        "version": 1, "documentary_only": True, "employee": doc.employee,
        "company": doc.company, "work_date": str(doc.work_date),
        "start": str(doc.authorization_start), "end": str(doc.authorization_end),
        "disposition": doc.historical_disposition, "declared_intervals": intervals,
        "declared_hours": hours, "break_is_estimate": bool(doc.get("historical_break_estimated")),
        "reference": doc.historical_reference, "source_file": source.name,
        "file_url": source.file_url, "sha256": hashlib.sha256(content).hexdigest(),
        "historical_payroll_date": str(doc.settlement_payroll_date or ""),
        "recorded_by": frappe.session.user, "recorded_on": str(now_datetime()),
        "notice": _(NOTICE),
    }, ensure_ascii=False, sort_keys=True)
    doc.status = "Documented"
    doc.approved_by = frappe.session.user
    doc.approved_on = now_datetime()
    doc.settlement_status = "Not Applicable"


def prevent_salary_link(doc, method=None):
    """Also reject manually linked payroll earnings, not only the settlement button."""
    if doc.get("ref_doctype") == DT and doc.get("ref_docname"):
        source = frappe.get_doc(DT, doc.ref_docname)
        frappe.db.get_value("Employee", source.employee, "name", for_update=True)
        source = frappe.get_doc(DT, doc.ref_docname, for_update=True)
        reject_settlement(source)
