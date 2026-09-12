"""Explicit, role-controlled manual attendance verification. Never settles payroll."""
import hashlib
import json
from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import cint, escape_html, flt, get_datetime, getdate, now_datetime

from powerpro.controllers.overtime import _reconcile, _reconciliation_rows
from powerpro.payroll_rules.manual_overtime import normalize_intervals, verification_roles
from powerpro.payroll_rules.overtime_work_call import derive_reconciliation_snapshot

SOURCE = "Manual Verification"
FINAL = {"Created", "Payroll Submitted", "Paid", "Credited", "Cancelled"}
AUDIT_FIELDS = (
    "reconciliation_source", "manual_verification_reason", "manual_worked_intervals",
    "manual_checkin_comparison", "reconciled_by", "reconciled_on",
    "actual_start", "actual_end", "verified_hours", "regular_35_hours", "regular_100_hours",
    "holiday_100_hours", "weekly_rest_hours", "night_hours", "missing_hours", "unapproved_hours",
    "adherence_percent", "late_minutes", "early_departure_minutes", "reconciliation_status",
    "reconciliation_warnings", "reconciliation_intervals", "unapproved_intervals", "source_checkins",
)


def _enabled_for_user(*, for_update=False):
    # Read current settings on every request; no privileged-role bypass or cached client decision.
    settings = (frappe.get_doc("DGII Payroll Settings", "DGII Payroll Settings", for_update=True)
                if for_update else frappe.get_single("DGII Payroll Settings"))
    return bool(
        cint(settings.get("enable_overtime_authorization"))
        and cint(settings.get("enable_manual_overtime_verification"))
        and verification_roles(settings.get("overtime_manual_verification_roles")).intersection(
            frappe.get_roles(frappe.session.user)
        )
    )


def _require_role(*, for_update=False):
    if not _enabled_for_user(for_update=for_update):
        frappe.throw(_("Manual overtime verification is disabled or your role is not permitted in DGII Payroll Settings."), frappe.PermissionError)


def _check_document(doc):
    if doc.get("auto_enrolled"):
        frappe.throw(_("Use Attendance Exceptions on the enrolled Work Call."))
    doc.check_permission("read")
    doc.check_permission("write")
    if doc.docstatus != 1 or doc.status != "Approved":
        frappe.throw(_("Only a submitted approved Overtime Authorization can be verified."))
    if doc.get("settlement_status") in FINAL:
        frappe.throw(_("Settled or cancelled attendance cannot be changed."))


def _load(authorization, *, lock=False):
    _require_role()
    doc = frappe.get_doc("Overtime Authorization", authorization)
    _check_document(doc)
    work_call = None
    if doc.overtime_work_call:
        work_call = frappe.get_doc("Overtime Work Call", doc.overtime_work_call)
        work_call.check_permission("read")
        work_call.check_permission("write")
        if lock:
            frappe.db.get_value(work_call.doctype, work_call.name, "name", for_update=True)
            work_call = frappe.get_doc(work_call.doctype, work_call.name, for_update=True)
        if work_call.docstatus != 1:
            frappe.throw(_("The source overtime work call must be submitted."))
    if lock:
        # Match the Work Call / Employee ordering used by Dieta payout and cancellation.
        frappe.db.get_value("Employee", doc.employee, "name", for_update=True)
        frappe.db.get_value(doc.doctype, doc.name, "name", for_update=True)
        doc = frappe.get_doc(doc.doctype, doc.name, for_update=True)
        _check_document(doc)
        _require_role(for_update=True)
        if (doc.overtime_work_call or None) != (work_call.name if work_call else None):
            frappe.throw(_("The authorization changed. Reopen the preview."))
    return doc, work_call


@frappe.whitelist()
def get_manual_verification_options(work_call=None, authorization=None):
    if not _enabled_for_user():
        return {"allowed": False, "rows": []}
    if bool(work_call) == bool(authorization):
        frappe.throw(_("Select one Work Call or one authorization."))
    if authorization:
        names = [authorization]
    else:
        call = frappe.get_doc("Overtime Work Call", work_call)
        if not frappe.has_permission(call.doctype, "write", doc=call) or call.docstatus != 1:
            return {"allowed": False, "rows": []}
        call.check_permission("read")
        names = frappe.get_all("Overtime Authorization", filters={
            "overtime_work_call": call.name, "docstatus": 1, "status": "Approved",
            "settlement_status": ["not in", list(FINAL)],
        }, pluck="name", order_by="work_date asc, employee_name asc")
    rows = []
    for name in names:
        doc = frappe.get_doc("Overtime Authorization", name)
        if not all(frappe.has_permission(doc.doctype, action, doc=doc) for action in ("read", "write")):
            continue
        if doc.docstatus != 1 or doc.status != "Approved" or doc.get("settlement_status") in FINAL:
            continue
        rows.append({key: doc.get(key) for key in (
            "name", "employee_name", "work_date", "authorization_start", "authorization_end",
            "maximum_hours", "reconciliation_status", "reconciliation_source",
        )})
        rows[-1]["completed_window"] = get_datetime(doc.authorization_end) <= now_datetime()
    return {"allowed": True, "rows": rows}


def _preview(doc, intervals, reason, *, for_update=False):
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 2000:
        frappe.throw(_("Enter a verification reason of 1 to 2000 characters."))
    try:
        rows = json.loads(intervals) if isinstance(intervals, str) else intervals
        rows = normalize_intervals(rows, authorization_start=doc.authorization_start,
                                   authorization_end=doc.authorization_end, now=now_datetime())
    except (ValueError, TypeError) as exc:
        frappe.throw(_(str(exc)))
    # Real check-ins remain distinct comparison evidence; no synthetic punches are created.
    comparison = _reconcile(doc, include_weekly_context=True, for_update=for_update)
    result = _reconcile(doc, include_weekly_context=True, manual_intervals=rows, for_update=for_update)
    snapshot = derive_reconciliation_snapshot(
        authorization_start=doc.authorization_start, authorization_end=doc.authorization_end,
        maximum_hours=doc.maximum_hours, reconciliation=result, evaluation_time=now_datetime(),
        evidence_source=SOURCE,
    )
    if snapshot["verified_hours"] <= 0:
        frappe.throw(_("The entered intervals contain no eligible overtime inside the approved window."))
    _validate_weekly_sequence(doc, snapshot, for_update=for_update)
    data = {
        "authorization": doc.name, "employee_name": doc.employee_name,
        "modified": str(doc.modified), "authorization_start": str(doc.authorization_start),
        "authorization_end": str(doc.authorization_end), "maximum_hours": doc.maximum_hours,
        "planned_settlement": doc.planned_settlement, "reason": reason.strip(),
        "intervals": rows, "snapshot": snapshot, "calculation": result,
        "checkin_comparison": comparison,
        "hours_difference": round(snapshot["verified_hours"] - flt(comparison.get("verified_hours")), 4),
        "read_only": True,
    }
    data["preview_token"] = hashlib.sha256(_json(data).encode()).hexdigest()
    return data


@frappe.whitelist()
def preview_manual_verification(authorization, intervals, reason):
    doc, _call = _load(authorization)
    return _preview(doc, intervals, reason)


@frappe.whitelist(methods=["POST"])
def approve_manual_verification(authorization, intervals, reason, preview_token):
    doc, call = _load(authorization, lock=True)
    preview = _preview(doc, intervals, reason, for_update=True)
    if not preview_token or preview_token != preview["preview_token"]:
        frappe.throw(_("Attendance or settings changed. Review a new preview before approving."))
    before = {field: doc.get(field) for field in AUDIT_FIELDS}
    values = {
        **preview["snapshot"], "reconciliation_source": SOURCE,
        "manual_verification_reason": preview["reason"],
        "manual_worked_intervals": _json(preview["intervals"]),
        "manual_checkin_comparison": _json(preview["checkin_comparison"]),
        "reconciliation_warnings": "\n".join(preview["calculation"]["warnings"]),
        "reconciliation_intervals": _json(preview["calculation"]["intervals"]),
        "unapproved_intervals": _json(preview["calculation"]["unapproved_intervals"]),
        "source_checkins": _json(preview["checkin_comparison"]["source_checkins"]),
        "reconciled_by": frappe.session.user, "reconciled_on": now_datetime(),
    }
    # One request transaction includes the snapshot, Dieta hooks, audit and team totals.
    doc.db_set(values)
    audit = {"before": before, "after": {field: doc.get(field) for field in AUDIT_FIELDS}}
    doc.add_comment("Info", _("Attendance manually verified by {0}.").format(escape_html(frappe.session.user))
                    + "<pre>" + escape_html(_json(audit)) + "</pre>")
    if call:
        _sync_work_call(call)
        call.add_comment("Info", _("Manual attendance verified for {0}: {1} hours. Reason: {2}").format(
            escape_html(doc.name), doc.verified_hours, escape_html(preview["reason"])))
    return {"authorization": doc.name, "verified_hours": doc.verified_hours,
            "reconciliation_status": doc.reconciliation_status, "settlement_status": doc.settlement_status}


def _validate_weekly_sequence(doc, snapshot, *, for_update=False):
    # A new earlier certification must not silently change the 35%/100% split of
    # later frozen payroll snapshots. Verify regular overtime chronologically.
    if not any(flt(item.get(field)) for item in (doc, snapshot)
               for field in ("regular_35_hours", "regular_100_hours")):
        return
    work_date = getdate(doc.work_date)
    week_end = work_date + timedelta(days=6 - work_date.weekday())
    for doctype in ("Overtime Authorization", "Retroactive Overtime Adjustment"):
        if not frappe.db.exists("DocType", doctype):
            continue
        rows = _reconciliation_rows(doctype, for_update=for_update, filters={
            "employee": doc.employee, "docstatus": 1,
            "work_date": ["between", [work_date, week_end]],
            "authorization_start": [">", doc.authorization_start],
            "verified_hours": [">", 0],
        }, fields=["name", "regular_35_hours", "regular_100_hours"])
        if any(flt(row.regular_35_hours) + flt(row.regular_100_hours) > 0 for row in rows):
            frappe.throw(_("Later overtime in this week already has verified payroll hours. Review that reconciliation before certifying earlier hours; verify regular overtime chronologically."))


def _sync_work_call(call):
    from powerpro.power_pro.doctype.overtime_work_call.overtime_work_call import _summarize
    rows = _reconciliation_rows("Overtime Authorization", for_update=True, filters={"overtime_work_call": call.name, "docstatus": 1},
                          fields=["maximum_hours as requested_hours", "verified_hours", "reconciliation_status"])
    if len(rows) != cint(call.authorization_count):
        frappe.throw(_("The Work Call's authorization set is incomplete."))
    summary = _summarize(rows)
    call.db_set({"status": summary["work_call_status"], "verified_hours": summary["verified_hours"],
                 "adherence_percent": summary["adherence_percent"],
                 "last_reconciled_by": frappe.session.user, "last_reconciled_on": now_datetime()})


def protect_manual_snapshot(doc):
    """Document-save APIs cannot forge or edit the audited manual snapshot."""
    before = doc.get_doc_before_save()
    if not before or before.docstatus != 1:
        if doc.get("reconciliation_source") == SOURCE or any(doc.get(field) for field in (
            "manual_verification_reason", "manual_worked_intervals", "manual_checkin_comparison"
        )):
            frappe.throw(_("Use Manual Attendance Verification to save attendance evidence."))
        return
    if before.get("reconciliation_source") != SOURCE and doc.get("reconciliation_source") != SOURCE:
        if any(before.get(field) != doc.get(field) for field in (
            "manual_verification_reason", "manual_worked_intervals", "manual_checkin_comparison"
        )):
            frappe.throw(_("Use Manual Attendance Verification to save attendance evidence."))
        return
    if any(before.get(field) != doc.get(field) for field in AUDIT_FIELDS):
        frappe.throw(_("Use Manual Attendance Verification to amend the audited attendance snapshot."))


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
